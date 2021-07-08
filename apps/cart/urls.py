from django.urls import path

from cart.views import CartInfoView, CartAddView, CartUpdateView, CartDeleteView

urlpatterns = [
    path('', CartInfoView.as_view(), name='show'),
    path('add',CartAddView.as_view(), name='add'),
    path('update',CartUpdateView.as_view(), name='update'),
    path('delete',CartDeleteView.as_view(), name='add'),
]