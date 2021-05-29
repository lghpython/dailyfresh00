from django.urls import path
from goods import views
from goods.views import IndexView

urlpatterns = [
    # path('', views.index, name='index'),
    path('index', IndexView.as_view(), name='index'),
    path('detail/(?P<goods_id>\d+)', IndexView.as_view(), name='detail'),
]