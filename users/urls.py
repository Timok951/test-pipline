from django.urls import path,include
from .views import *
from shop.views import home
urlpatterns = [
    path('', home, name='home'),
    path('login/', login_user, name='login'),
    path('registration/', registration_user, name='registration_page'),
    path('logout/', logout_user, name='logout_page'),
    path('profile/', profile_page, name='profile_page'),
    path('settings/', user_settings, name='user_settings'),
]
