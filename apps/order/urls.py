from django.urls import path, re_path

from cart.views import CartInfoView
from goods import views
from order.views import OrderPlaceView, OrderPayView, CommentView, OrderCommitView, PayCheckView

urlpatterns = [
    path('place', OrderPlaceView.as_view(), name='place'),
    path('commit', OrderCommitView.as_view(), name='commit'),
    path('pay', OrderPayView.as_view(), name='pay'),
    path('check', PayCheckView.as_view(), name='pay'),
    re_path('^comment/(?P<order_id>\d+)$', CommentView.as_view(), name='comment'),
]
