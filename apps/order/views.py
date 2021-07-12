import os
from datetime import datetime

from alipay import AliPay
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.views import View
from django_redis import get_redis_connection

from dailyfresh00 import settings
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
            return redirect(reversed('cart:show'))

        conn = get_redis_connection('default')
        cart_key = 'cart_%d' % user.id

        skus = []

        total_count = 0
        total_price = 0

        for sku_id in sku_ids:
            sku = GoodsSKU.objects.get(id=sku_id)
            count = conn.hget(cart_key, sku_id)
            amount = sku.price * int(count)

            sku.count = int(count)
            sku.amount = amount
            skus.append(sku)
            total_count += int(count)
            total_price += amount

        # 运费为独立子系统， 这里写死
        transit_place = 10
        total_pay = total_price + transit_place

        # 获取用户地址
        addrs = Address.objects.filter(user=user)

        # 整合上下文
        sku_ids = ','.join(sku_ids)
        context = {
            'skus': skus,
            'total_price': total_price,
            'total_count': total_count,
            'total_pay': total_pay,
            'addrs': addrs,
            'transit_place': transit_place,
            'sku_ids': sku_ids,
        }

        return render(request, 'place_order.html', context)


class OrderCommitView(View):
    """ 订单提交页面"""

    # 设置该函数为一个事务
    @transaction.atomic
    def post(self, request):
        user = request.user
        if not user.is_authenticated:
            return JsonResponse({'res': 0, 'errmsg': '用户未登录'})
        # 获取请求数据
        pay_method = request.POST.get('pay_method')
        sku_ids = request.POST.get('sku_ids')
        addr_id = request.POST.get('addr_id')
        # print(sku_ids)
        # 校验数据完整性
        if not ([pay_method, sku_ids, addr_id]):
            return JsonResponse({'res': 1, 'errmsg': '数据不完整'})

        if pay_method not in OrderInfo.PAY_METHODS.keys():
            return JsonResponse({'res': 2, 'errmsg': '非法的支付方法'})
        try:
            addr = Address.objects.get(id=addr_id)
        except Address.DoesNotExist:
            return JsonResponse({'res': 3, 'errmsg': '非法的地址'})

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
            print('s', order_id, user, addr, total_price, total_count, transit_price, pay_method)
            order = OrderInfo.objects.create(
                order_id=order_id,
                user=user,
                addr=addr,
                transit_price=transit_price,
                pay_method=pay_method
            )
            # todo: 用户的订单中有几个商品，需要向df_order_goods表中加入几条记录
            conn = get_redis_connection('default')
            cart_key = 'cart_%d' % user.id

            sku_ids = sku_ids.split(',')
            # print(sku_ids)
            for sku_id in sku_ids:
                try:
                    print(sku_id)
                    # 悲观锁 ， 处理订单并发， 拿到锁，阻塞其他用户， 事务结束释放
                    # 搜索时加锁， select_for_update()  一个拿到，其他阻塞， 处理订单并发
                    sku = GoodsSKU.objects.select_for_update().get(id=sku_id)

                except GoodsSKU.DoesNotExist:
                    # 回滚事务保存点
                    transaction.savepoint_rollback(save_id)
                    return JsonResponse({'res': 4, 'errmsg': '商品不存在'})

                import time
                time.sleep(5)

                count = conn.hget(cart_key, sku_id)
                count = int(count)
                if count > sku.stock:
                    transaction.savepoint_rollback(save_id)
                    return JsonResponse({'res': 6, 'errmsg': '商品库存不足'})

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
            return JsonResponse({'res': 7, 'errmsg': '下单失败'})

        transaction.savepoint_commit(save_id)
        conn.hdel(cart_key, *sku_ids)
        return JsonResponse({'res': 5, 'message': '创建成功'})


class OrderPayView(View):
    def post(self, request):
        # todo:获取用户数据， 校验登录
        user = request.user
        if not user.is_authenticated:
            return JsonResponse({'res': 0, 'errmsg': '用户未登录'})

        # todo: 接受参数
        order_id = request.POST.get('order_id')
        if not order_id:
            return JsonResponse({'res': 1, 'errmsg': '参数接收失败'})

        # todo: 获取订单数据
        try:
            order = OrderInfo.objects.get(order_id=order_id)
        except OrderInfo.DoesNotExist:
            return JsonResponse({'res': 2, 'errormsg': '订单不存在'})

        # todo: 业务处理:使用python sdk调用支付宝的支付接口
        # 初始化
        print('alipay 初始化')
        app_private_key_string = open(os.path.join(settings.BASE_DIR, 'apps/order/app_private_key.pem')).read()
        alipay_public_key_string = open(os.path.join(settings.BASE_DIR, 'apps/order/alipay_public_key.pem')).read()
        alipay = AliPay(
            appid="2021000117687593",
            app_notify_url=None,  # 默认回调 url
            app_private_key_string=app_private_key_string,
            # 支付宝的公钥，验证支付宝回传消息使用，不是你自己的公钥,
            alipay_public_key_string=alipay_public_key_string,
            sign_type="RSA2",  # RSA 或者 RSA2
            debug=True,  # 默认 False
        )
        print('接入接口', order_id)
        # 电脑支付接口， 'https://openapi.alipaydev.com/gateway.do?'+order_string
        total_pay = order.total_price + order.transit_price
        print(order_id, total_pay)
        order_string = alipay.api_alipay_trade_page_pay(
            out_trade_no=order_id,
            total_amount=str(total_pay),
            subject="天天生鲜%s" % order_id,
            return_url=None,
            notify_url=None
        )
        print(order_string)
        #  返回应答 https://openapi.alipaydev.com/gateway.do
        pay_url = 'https://openapi.alipaydev.com/gateway.do?' + order_string
        print(pay_url)
        return JsonResponse({'res': 3, 'pay_url': pay_url})


class PayCheckView(View):
    def post(self, request):
        # todo: 校验用户登录
        user = request.user
        if not user.is_authenticated:
            return JsonResponse({'res': 0, 'errmsg': '用户未登录'})

        # todo: 接受参数
        order_id = request.POST.get('order_id')
        if not order_id:
            return JsonResponse({'res': 1, 'errmsg': '订单id失败'})

        # todo: 获取订单数据
        try:
            # 获取订单 其他支付方式未实现，这里统一支付宝支付未支付订单
            print(order_id, user)
            # order = OrderInfo.objects.get(order_id=order_id， user=user, order_status=1)
            order = OrderInfo.objects.get(order_id=order_id, user=user, order_status=1, pay_method=3)
        except OrderInfo.DoesNotExist:
            return JsonResponse({'res': 2, 'errmsg': '订单错误'})

        # todo: 业务处理:使用python sdk调用支付宝的查询接口、
        # 初始化
        print('alipay 初始化')
        app_private_key_string = open(os.path.join(settings.BASE_DIR, 'apps/order/app_private_key.pem')).read()
        alipay_public_key_string = open(os.path.join(settings.BASE_DIR, 'apps/order/alipay_public_key.pem')).read()
        alipay = AliPay(
            appid="2021000117687593",
            app_notify_url=None,  # 默认回调 url
            app_private_key_string=app_private_key_string,
            # 支付宝的公钥，验证支付宝回传消息使用，不是你自己的公钥,
            alipay_public_key_string=alipay_public_key_string,
            sign_type="RSA2",  # RSA 或者 RSA2
            debug=True,  # 默认 False
        )

        while True:
            print('查询支付结果')
            # 查询
            response = alipay.api_alipay_trade_query(out_trade_no=order_id)
            # "alipay_trade_query_response":
            # {"trade_no": "2017032121001004070200176844",
            #  "code": "10000",
            #  "invoice_amount": "20.00",
            #  "open_id": "20880072506750308812798160715407",
            #  "fund_bill_list": [{"amount": "20.00", "fund_channel": "ALIPAYACCOUNT"}],
            #  "buyer_logon_id": "csq***@sandbox.com",
            #  "send_pay_date": "2017-03-21 13:29:17",
            #  "receipt_amount": "20.00",
            #  "out_trade_no": "out_trade_no15",
            #  "buyer_pay_amount": "20.00",
            #  "buyer_user_id": "2088102169481075",
            #  "msg": "Success", "point_amount": "0.00",
            #  "trade_status": "TRADE_SUCCESS",
            #  "total_amount": "20.00"},
            print(response)

            code = response.get('code')
            print('循环中', code)
            if code == '10000' and response.get('trade_status') == "TRADE_SUCCESS":
                trade_no = response.get('trade_no')
                order.trade_no = trade_no
                order.order_status = 4  # 待评价
                order.save()
                return JsonResponse({'res': 3, 'message': '支付成功'})
            elif code == '40004' or code == '10000' and response.get('trade_status') == "WAIT_BUYER_PAY":
                # 等待卖家付款
                # 业务处理失败
                import time
                time.sleep(5)
                print('循环中', code)
                continue

            else:
                print(code)
                return JsonResponse({'res': 4, 'errmsg': '用户未支付'})


class CommentView(LoginRequiredMixin, View):
    def get(self, request):
        user = request.user
        if not user.is_authenticated:
            return JsonResponse({'res': 0, 'errmsg': '用户未登录'})

        # todo: 接受参数
        order_id = request.POST.get('order_id')
        if not order_id:
            return JsonResponse({'res': 1, 'errmsg': '订单id失败'})

        # todo: 获取订单数据
        try:
            # 获取订单 其他支付方式未实现，这里统一支付宝支付未支付订单
            print(order_id, user)
            # order = OrderInfo.objects.get(order_id=order_id， user=user, order_status=1)
            order = OrderInfo.objects.get(order_id=order_id, user=user, order_status=1, pay_method=3)
        except OrderInfo.DoesNotExist:
            return JsonResponse({'res': 2, 'errmsg': '订单错误'})

    def post(self, request):
        user = request.user
        if not user.is_authenticated:
            return JsonResponse({'res': 0, 'errmsg': '用户未登录'})

        # todo: 接受参数
        order_id = request.POST.get('order_id')
        if not order_id:
            return JsonResponse({'res': 1, 'errmsg': '订单id失败'})

        # todo: 获取订单数据
        try:
            # 获取订单 其他支付方式未实现，这里统一支付宝支付未支付订单
            print(order_id, user)
            # order = OrderInfo.objects.get(order_id=order_id， user=user, order_status=1)
            order = OrderInfo.objects.get(order_id=order_id, user=user, order_status=1, pay_method=3)
        except OrderInfo.DoesNotExist:
            return JsonResponse({'res': 2, 'errmsg': '订单错误'})
