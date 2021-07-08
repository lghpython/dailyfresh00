from django.urls import path

from cart.views import CartInfoView
from goods import views
from order.views import OrderPlaceView, OrderPayView, CommentView

urlpatterns = [
    path('place', OrderPlaceView.as_view(), name='place'),
    path('commit', OrderPlaceView.as_view(), name='commit'),
    path('pay', OrderPayView.as_view(), name='pay'),
    path('comment', CommentView.as_view(), name='comment'),
]