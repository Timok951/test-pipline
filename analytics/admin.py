from django.contrib import admin
from simple_history.models import HistoricalRecords
from .models import *

admin.site.register(UserOrders)
admin.site.register(GoodIncome)
admin.site.register(DangerousGoods)
admin.site.register(OrderReport)
