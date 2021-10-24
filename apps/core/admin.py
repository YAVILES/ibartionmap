from django.contrib import admin

# Register your models here.

from .models import SynchronizedTables, DataGroup, RelationsTable

admin.site.register(SynchronizedTables)
admin.site.register(DataGroup)
admin.site.register(RelationsTable)
