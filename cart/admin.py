from django.contrib import admin
from .models import *
from simple_history.admin import SimpleHistoryAdmin

admin.site.register(Order, SimpleHistoryAdmin)
admin.site.register(OrderItem, SimpleHistoryAdmin)
