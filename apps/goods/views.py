from django.shortcuts import render, redirect
from django.views import View

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
        context = {'index_goods_banner': index_goods_banner,
                   'index_promotion_banner': index_promotion_banner,
                   'types': types,
                   }
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
        # 获取同一个SPU的其他规格商品

        context = {'sku': sku, 'types': types}

        return render(request,'detail.html',context)


class ListView(View):
    def get(self,request, type):
        # 获取类型列表信息
        goods = GoodsSKU.objects.filter(type=type).all()
        context={
            'goods': goods
        }
        return render(request, 'list.html', context)
