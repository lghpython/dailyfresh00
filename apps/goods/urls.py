from django.urls import path, re_path
from goods import views
from goods.views import IndexView, ListView, DetailView

urlpatterns = [
    # path('', views.index, name='index'),
    path('index', IndexView.as_view(), name='index'),
    re_path('^detail/(?P<goods_id>\d+)$', DetailView.as_view(), name='detail'),
    re_path('^list/(?P<type_id>\d+)/(?P<page>\d+)$', ListView.as_view(), name='list'),
]