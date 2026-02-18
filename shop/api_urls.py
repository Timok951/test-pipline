from django.urls import path
from . import api

urlpatterns = [
    path("goods/", api.goods_api, name="api_goods"),
    path("goods/<int:pk>/", api.good_detail_api, name="api_good_detail"),
    path("orders/", api.orders_api, name="api_orders"),
    path("orders/checkout/", api.orders_checkout_api, name="api_orders_checkout"),
]
