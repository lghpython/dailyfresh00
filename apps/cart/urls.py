from django.urls import path

from cart.views import CartInfoView
from goods import views


urlpatterns = [
    path('', CartInfoView.as_view(), name='show'),
]