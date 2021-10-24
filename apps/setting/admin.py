from django.contrib import admin

# Register your models here.
from apps.setting.models import Connection

admin.site.register(Connection)