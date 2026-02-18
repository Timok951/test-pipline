from django.contrib import admin
from .models import *
from simple_history.admin import SimpleHistoryAdmin

admin.site.register(Tag, SimpleHistoryAdmin)
admin.site.register(Company, SimpleHistoryAdmin)
admin.site.register(Type, SimpleHistoryAdmin)
admin.site.register(Good, SimpleHistoryAdmin)
admin.site.register(Rate, SimpleHistoryAdmin)


