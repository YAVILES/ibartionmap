from django.contrib import admin

# Register your models here.

from .models import SynchronizedTables, RelationsTable

admin.site.register(SynchronizedTables)
admin.site.register(RelationsTable)
