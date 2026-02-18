from django.urls import path,include
from .views import *
urlpatterns = [
    path('', home, name="home"),
    
    #Arguments
    path('good/<int:pk>', good_page ,name='good_page'),
    path('good/<int:pk>/favorite/', toggle_favorite, name='toggle_favorite'),
    path('good/<int:pk>/review/', add_review, name='add_review'),
    path('warehouse/', warehouse_dashboard, name='warehouse_dashboard'),
    path('warehouse/add-cost/', warehouse_add_cost, name='warehouse_add_cost'),
    path('warehouse/add-stock/', warehouse_add_stock, name='warehouse_add_stock'),
    path('warehouse/delete-bad/', warehouse_delete_bad_goods, name='warehouse_delete_bad_goods'),
    path('warehouse/goods/create/', warehouse_good_create, name='warehouse_good_create'),
    path('warehouse/goods/<int:pk>/edit/', warehouse_good_edit, name='warehouse_good_edit'),
    path('warehouse/goods/<int:pk>/delete/', warehouse_good_delete, name='warehouse_good_delete'),
    path('api/', include('shop.api_urls')),

]
