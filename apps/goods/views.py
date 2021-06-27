from django.core.cache import cache
from django.core.paginator import Paginator
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views import View
from django_redis import get_redis_connection

from goods.models import GoodsType, IndexGoodsBanner, IndexPromotionBanner, IndexGoodsTypeBanner, GoodsSKU

"""
def index(request):
    # 获取商品类型
    types = GoodsType.objects.all()
    # 获取商品轮播数据
    index_goods_banner = IndexGoodsBanner.objects.all().order_by('index')
    # 获取商品促销活动数据
    index_promotion_banner = IndexPromotionBanner.objects.all.order_by('index')

    # 获取商品分类展示数据
    for type in types:
        title_banners = IndexGoodsTypeBanner.objects.filter(type=type, display_type=0).order_by('index')
        image_banners = IndexGoodsTypeBanner.objects.filter(type=type, display_type=1).order_by('index')
        type.title_banners = title_banners
        type.image_banners = image_banners

    # 上下文整合数据
    context = {'index_goods_banner':index_goods_banner,
               'index_promotion_banner':index_promotion_banner,
               'types': types,
               }
    return render(request, 'index.html', context)"""


class IndexView(View):
    def get(self, request):
        context = cache.get('static_index_html')
        # print(context)
        # context = None
        if context is None:
            # 获取商品类型
            types = GoodsType.objects.all()
            # 获取商品轮播数据
            index_goods_banner = IndexGoodsBanner.objects.all().order_by('index')
            # 获取商品促销活动数据
            index_promotion_banner = IndexPromotionBanner.objects.all().order_by('index')

            # 获取商品分类展示数据
            for type in types:
                title_banners = IndexGoodsTypeBanner.objects.filter(type=type, display_type=0).order_by('index')
                image_banners = IndexGoodsTypeBanner.objects.filter(type=type, display_type=1).order_by('index')
                type.title_banners = title_banners
                type.image_banners = image_banners

            # 上下文整合数据
            context = {'index_goods_banner': index_goods_banner,
                       'index_promotion_banner': index_promotion_banner,
                       'types': types,
                       }
            cache.set('static_index_html', context, 60 * 60 * 1)

        # 获取购物车数量 登录用户获取购物车数量
        cart_count = 0
        user = request.user
        if user.is_authenticated:
            conn = get_redis_connection('default')
            cart_key = "cart_%d" % user.id
            cart_count = conn.hlen(cart_key)

        context.update(cart_count=cart_count)
        # print(context)
        return render(request, 'index.html', context)


class DetailView(View):
    def get(self, request, goods_id):
        # 商品goods_id, 获取商品sku 数据
        try:
            sku = GoodsSKU.objects.get(id=goods_id)
        except GoodsSKU.DoesNotExist:
            redirect(reversed('good:index'))
        # 获取商品类型
        types = GoodsType.objects.all()

        # 获取商品评论信息

        # 获取新品信息
        new_skus = GoodsSKU.objects.filter(type=sku.type).order_by("-create_time")[:2]
        # 获取同一个SPU的其他规格商品
        same_spu_skus = GoodsSKU.objects.all().exclude(id=goods_id)
        user = request.user
        cart_count = 0
        if user.is_authenticated:
            # 购物车计数
            conn = get_redis_connection('default')
            cart_key = 'cart_%d' % user.id
            cart_count = conn.hlen(cart_key)

            # redis 缓存浏览记录
            conn = get_redis_connection('default')
            history_key = 'history_%d' % user.id
            # 移除已存在的goods_id
            conn.lrem(history_key, 0, goods_id)
            # 首位添加goods_id
            conn.lpush(history_key, goods_id)
            # 保留前5个历史记录
            conn.ltrim(history_key, 0, 4)

        context = {'sku': sku,
                   'types': types,
                   'new_skus': new_skus,
                   'same_spu_skus': same_spu_skus,
                   'cart_count': cart_count,
                   }

        return render(request, 'detail.html', context)


class ListView(View):
    def get(self, request, type_id, page):
        '''显示列表页'''
        # 获取所属类型
        try:
            type = GoodsType.objects.get(id=type_id)
        except GoodsType.DoesNotExists:
            return redirect(reverse('goods:index'))
        types = GoodsType.objects.all()

        # 获取该类型 所有商品信息
        skus = GoodsSKU.objects.filter(type=type).all()
        sort = request.GET.get('sort')
        # 以不同排序展示列表商品
        if sort == 'hot':
            skus = GoodsSKU.objects.filter(type=type).order_by('-sales')
        elif sort == 'price':
            skus = GoodsSKU.objects.filter(type=type).order_by('price')
        else:
            sort = 'default'
            skus = GoodsSKU.objects.filter(type=type).order_by('-id')

        # 对数据分页
        paginator = Paginator(skus, 1)

        # 页面不在正确范围， 显示首页
        try:
            page = int(page)
        except Exception as e:
            page = 1


        num_pages = paginator.num_pages
        if page > paginator.num_pages:
            page = 1

        # 获取第page页的Page实例对象
        skus_page = paginator.page(page)
        print(page,num_pages)

        if num_pages < 5:
            pages = range(1, num_pages + 1)
        elif page <= 3:
            pages = range(1, 6)
        elif num_pages - page <= 2:
            pages = range(num_pages-4, num_pages + 1)
        else:
            pages = range(page-2, page+3)
        print(pages)
        skus_page = paginator.page(page)
        # 获取新品信息
        new_skus = GoodsSKU.objects.filter(type=type).order_by('-create_time')[:2]

        # 获取用户购物车中商品的数目
        user = request.user
        cart_count = 0
        if user.is_authenticated:
            # 用户已登录
            conn = get_redis_connection('default')
            cart_key = 'cart_%d' % user.id
            cart_count = conn.hlen(cart_key)

        context = {
            'type':type,
            'types':types,
            'sort':sort,
            'cart_count': cart_count,
            'pages': pages,
            'skus_page': skus_page,
            'new_skus': new_skus,
        }
        # print(context)
        return render(request, 'list.html', context)
