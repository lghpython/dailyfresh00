from django.contrib import admin

from order.models import OrderInfo

admin.site.register(OrderInfo, admin.ModelAdmin)
