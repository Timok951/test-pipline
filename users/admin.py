from django.contrib import admin
from .models import *
from simple_history.admin import SimpleHistoryAdmin
from .forms import *

# Register your models here.
admin.site.register(Role)
admin.site.register(User)
admin.site.register(UserCredenetials)
admin.site.register(UserFavorites)

