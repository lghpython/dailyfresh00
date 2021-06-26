from django.urls import path, re_path
from goods import views
from goods.views import IndexView, ListView

urlpatterns = [
    # path('', views.index, name='index'),
    path('index', IndexView.as_view(), name='index'),
    re_path('^detail/(?P<goods_id>\d+)$', IndexView.as_view(), name='detail'),
    re_path('^list/(?P<type_id>\d+)$', ListView.as_view(), name='list'),
]