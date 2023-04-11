from django.contrib import admin
from .models import *


class FosTypeAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'created_at', 'updated_at')
    list_display_links = ('id', 'name')
    search_fields = ('id', 'name')


admin.site.register(FosType, FosTypeAdmin)
