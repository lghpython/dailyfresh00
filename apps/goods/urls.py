from django.urls import path
from goods import views
from goods.views import IndexView, ListView

urlpatterns = [
    # path('', views.index, name='index'),
    path('index', IndexView.as_view(), name='index'),
    path('detail/(?P<goods_id>\d+)', IndexView.as_view(), name='detail'),
    path('list/(?P<type_id>\d+)', ListView.as_view(), name='list'),
]