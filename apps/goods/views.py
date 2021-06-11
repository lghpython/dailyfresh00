from django.core.cache import cache
from django.shortcuts import render, redirect
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
            cache.set('static_index_html',context, 60*60*1)

            # 获取购物车
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
        new_skus = GoodsSKU.objects.filter("-create_time")[:2]
        # 获取同一个SPU的其他规格商品
        same_spu_skus = GoodsSKU.objects.all().exclude(id=goods_id)
        user = request.user
        cart_count = 0
        if user.is_authenticated():
            # 购物车计数

            # redis 缓存浏览记录
            conn = get_redis_connection('default')
            history_key = 'history_%d'.user.id
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
    def get(self, request, type):
        # 获取类型列表信息
        sku = GoodsSKU.objects.filter(type=type).all()



        context = {
            'sku': sku,
        }
        return render(request, 'list.html', context)
