from datetime import datetime

from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import render
from django.views import View
from django_redis import get_redis_connection

from goods.models import GoodsSKU
from order.models import OrderInfo, OrderGoods
from user.models import Address
from utils.mixin import LoginRequiredMixin


class OrderPlaceView(LoginRequiredMixin, View):
    def post(self, request):
        # 获取用户数据
        user = request.user

        # 获取购物车提交的订单商品id
        sku_ids = request.POST.getlist('sku_ids')

        if not sku_ids:
            # 返回购物车页面
            return render(reversed('cart:show'))

        conn = get_redis_connection('default')
        cart_key = 'cart_%d'%user.id

        skus =[]

        total_count = 0
        total_price = 0

        for sku_id in sku_ids:
            sku = GoodsSKU.objects.get(id=sku_id)
            count = conn.hget(cart_key,sku_id)
            amount = sku.price * int(count)

            sku.count = count
            sku.amount = amount
            skus.append(sku)
            total_count += int(count)
            total_price += amount

        # 运费为独立子系统， 这里写死
        transit_place = 10
        total_pay = total_price + transit_place

        # 获取用户地址
        addrs = Address.objects.get(user=user)

        # 整合上下文
        sku_ids = ','.join(sku_ids)
        context = {
            'skus': skus,
            'total_price':total_price,
            'total_count': total_count,
            'total_pay':total_pay,
            'addrs':addrs,
            'transit_place':transit_place,
            'sku_ids':sku_ids,
        }

        return render(request, 'place_order.html', context)


class OrderCommitView(View):
    """ 订单提交页面"""
    @transaction.atomic
    def post(self, request):
        user = request.user
        if user.is_authenticated:
            return JsonResponse({'res':0, 'errmsg':'用户未登录'})
        # 获取请求数据
        pay_method = request.POST.get('pay_method')
        sku_ids = request.POST.get('sku_ids')
        addr_id = request.POST.get('addr_id')
        # 校验数据完整性
        if not([pay_method, sku_ids, addr_id]):
            return JsonResponse({'res':1, 'errmsg':'数据不完整'})

        if pay_method not in OrderInfo.PAY_METHODS.keys(self):
            return JsonResponse({'res':2, 'errmsg':'非法的支付方法'})
        try:
            address = Address.objects.get(id=addr_id)
        except Address.DoesNotExist:
            return JsonResponse({'res':3, 'errmsg':'非法的地址'})

        # todo: 创建订单核心业务
        # 订单id: 但钱时间+用户id
        order_id = datetime.now().strftime('%Y%m%d%H%M%S') + str(user.id)
        # 运费
        transit_price = 10
        # 保存时吾保存点
        save_id = transaction.savepoint()
        total_price = 0
        total_count = 0
        try:
            order = OrderInfo.objects.create(
                order_id=order_id,
                user=user,
                address=address,
                total_price=total_price,
                total_count=total_count,
                transit_place=transit_price,
                pay_method=pay_method,

            )
            # todo: 用户的订单中有几个商品，需要向df_order_goods表中加入几条记录
            conn = get_redis_connection('default')
            cart_key = 'cart_%d' % user.id

            sku_ids = sku_ids.split(',')
            for sku_id in sku_ids:
                try:
                    sku = GoodsSKU.objects.select_for_update().get(id=sku_id)

                except GoodsSKU.DoesNotExist:
                    # 回滚事务保存点
                    transaction.savepoint_rollback(save_id)
                    return JsonResponse({'res':4, 'errmsg':'商品不存在'})

                import time
                time.sleep(10)

                count = conn.hget(cart_key,sku_id)
                count = int(count)
                if count>sku.stock:
                    transaction.savepoint_rollback(save_id)
                    return JsonResponse({'res':6, 'errmsg':'商品库存不足'})

                OrderGoods.objects.create(
                    order=order,
                    sku=sku,
                    price=sku.price,
                    count=count,
                )
                # todo: 更新商品库存和销量
                sku.stock -= count
                sku.sales += count
                sku.save()
                # todo: 计算商品总价
                amount = sku.price * count
                total_price += amount
                total_count += count
            # todo: 更新订单总价格，总数量
            order.total_price = total_price
            order.total_count = total_count
            order.save()
        except:
            transaction.savepoint_rollback(save_id)
            return JsonResponse({'res':7, 'errmsg':'下单失败'})

        transaction.savepoint_commit(save_id)
        conn.hdel(cart_key,*sku_ids)
        return JsonResponse({'res':7,'message':'返回成功'})



class OrderPayView(LoginRequiredMixin, View):
    def post(self,request):
        user = request.user


class CommentView(LoginRequiredMixin, View):
    def get(self,request):
        user = request.user

    def post(self,request):
        user = request.user