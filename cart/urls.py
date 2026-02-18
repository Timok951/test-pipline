from django.urls import path,include
from .views import *

urlpatterns = [
    path('', cart_summarry, name="cart_summarry"),
    path('add/<int:pk>/', cart_add, name='cart_add'),
    path('delete/<int:pk>/', cart_delete, name='cart_delete'),
    path('update/<int:pk>/', cart_update, name='cart_update'),
    path('checkout/', cart_checkout, name='cart_checkout'),
]
