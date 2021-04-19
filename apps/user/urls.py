from django.urls import path, re_path

from user.views import RegisterView, LoginView, UserInfoView, UserOrderView, LogoutView, ActiveView, AddressView

urlpatterns = [
    path('register', RegisterView.as_view(), name='register'),
    path('login', LoginView.as_view(), name='login'),
    path('logout', LogoutView.as_view(), name='logout'),
    path('', UserInfoView.as_view(), name='user'),
    path('address', AddressView.as_view(), name='address'),
    re_path(r'^order/(?P<page>\d+)$', UserOrderView.as_view(), name='order'),  # 用户中心-订单页
    re_path(r'^active/(?P<token>.*)$', ActiveView.as_view(), name='active'),  # 用户中心-订单页
]
