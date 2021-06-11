from django.contrib import admin
from django.db import models

from goods.models import GoodsType, IndexPromotionBanner, IndexGoodsTypeBanner, IndexGoodsBanner


class BaseModelAdmin(admin.ModelAdmin):
    def save_model(self, request, obj, form, change):
        super().save_model(self, request, obj, form, change)
        from celery_tasks.tasks import generate_static_index_html
        generate_static_index_html.delay()

    def delete_model(self, request, obj):
        super().delete_model(self, request, obj)
        from celery_tasks.tasks import generate_static_index_html
        generate_static_index_html.delay()

class GoodsTypeModelAdmin(BaseModelAdmin):
    pass

class IndexPromotionBannerModelAdmin(BaseModelAdmin):
    pass

class IndexGoodsTypeBannerModelAdmin(BaseModelAdmin):
    pass

class IndexGoodsBannerModelAdmin(BaseModelAdmin):
    pass


admin.site.register(GoodsType, GoodsTypeModelAdmin)
admin.site.register(IndexPromotionBanner, IndexPromotionBannerModelAdmin)
admin.site.register(IndexGoodsTypeBanner, IndexGoodsTypeBannerModelAdmin)
admin.site.register(IndexGoodsBanner, IndexGoodsBannerModelAdmin)