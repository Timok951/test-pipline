from django.contrib.auth import login, logout
from users.metrics import *

class AuthService:
    def login_user(request,user):
        login(request,user)
        login_counter.inc()#update login counter
        update_metrics()#update gauges