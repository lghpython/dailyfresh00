from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import render
from django.views import View
from django_redis import get_redis_connection

from goods.models import GoodsSKU


class CartAddView(View):
    def post(self, request):
        # 获取用户数据
        user = request.user
        if not user.is_authenticated:
            return JsonResponse({'res': 0, 'errmsg': '用户未登录'})
        #  获取请求参数
        sku_id = request.POST.get('sku_id')
        count = request.POST.get('count')
        # 校验数据完整性
        if not all([sku_id, count]):
            return JsonResponse({'res': 1, 'errmsg': '数据不完整'})

        try:
            count = int(count)
        except Exception as e:
            return JsonResponse({'res': 2, 'errmsg': '商品数量出错'})

        # 数据库校验
        try:
            sku = GoodsSKU.objects.get(id=sku_id)
        except GoodsSKU.DoesNotExist:
            return JsonResponse({'res': 3, 'errmsg': '商品不存在'})

        conn = get_redis_connection('default')
        cart_key = 'cart_%d' % user.id
        cart_count = conn.hget(cart_key, sku_id)
        # 商品库存校验
        if cart_count:
            # 累加购物车中商品的数目
            count += int(cart_count)
        if count > sku.stock:
            return JsonResponse({'res': 4, 'errmsg': '商品数量超出库存'})
        conn.hset(cart_key, sku_id, count)
        total_count = conn.hlen(cart_key)
        return JsonResponse({'res': 5, 'total_count': total_count, 'massage': '返回成功'})


class CartInfoView(LoginRequiredMixin, View):
    def get(self, request):
        # 获取用户数据
        user = request.user

        # 从缓存中提取数据
        conn = get_redis_connection('default')
        cart_key = 'cart_%d' % user.id
        cart_dict = conn.hgetall(cart_key)
        # 获取数据库商品详情
        skus = []
        total_price = 0
        total_count = 0
        for sku_id, count in cart_dict.items():
            sku = GoodsSKU.objects.get(id=sku_id)
            amount = sku.price * int(count)
            # sku动态添加属性， 总价格、总数量
            sku.amount = amount
            sku.count = int(count)

            skus.append(sku)

            total_price += amount
            total_count += int(count)
        # print(skus)
        context = {
            'total_price': total_price,
            'total_count': total_count,
            'skus': skus
        }
        return render(request, 'cart.html', context)


class CartUpdateView(View):
    def post(self, request):
        # 用户验证
        user = request.user
        if not user.is_authenticated:
            return JsonResponse({'res': 0, 'errmsg': '用户未登录'})
        #  获取请求参数
        sku_id = request.POST.get('sku_id')
        count = request.POST.get('count')
        # 校验数据完整性
        if not all([sku_id, count]):
            return JsonResponse({'res': 1, 'errmsg': '数据不完整'})

        try:
            count = int(count)
        except Exception as e:
            return JsonResponse({'res': 2, 'errmsg': '商品数量出错'})

        # 数据库校验
        try:
            sku = GoodsSKU.objects.get(id=sku_id)
        except GoodsSKU.DoesNotExist:
            return JsonResponse({'res': 3, 'errmsg': '商品不存在'})

        conn = get_redis_connection('default')
        cart_key = 'cart_%d' % user.id

        # 商品库存校验
        if count > sku.stock:
            return JsonResponse({'res': 4, 'errmsg': '商品数量超出库存'})
        conn.hset(cart_key, sku_id, count)

        # 统计购物车商品总数
        total_count =0
        vals = conn.hvals(cart_key)
        for val in vals:
            total_count += int(val)

        return JsonResponse({'res': 5, 'total_count': total_count, 'massage': '返回成功'})


class CartDeleteView(View):
    def post(self, request):
        # 用户验证
        user = request.user
        if not user.is_authenticated:
            return JsonResponse({'res': 0, 'errmsg': '用户未登录'})
        #  获取商品id
        sku_id = request.POST.get('sku_id')
        if not sku_id:
            return JsonResponse({'res': 1, 'errmsg': '数据不完整'})

        # 数据库校验
        try:
            sku = GoodsSKU.objects.get(id=sku_id)
        except GoodsSKU.DoesNotExist:
            return JsonResponse({'res': 2, 'errmsg': '商品不存在'})

        conn = get_redis_connection('default')
        cart_key = 'cart_%d' % user.id
        # 删除购物车记录
        conn.hdel(cart_key, sku_id)
        # 统计购物车商品总数
        total_count =0
        vals = conn.hvals(cart_key)
        for val in vals:
            total_count += int(val)

        return JsonResponse({'res': 3, 'total_count': total_count, 'massage': '返回成功'})
