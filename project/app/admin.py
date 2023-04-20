from adminfilters.autocomplete import AutoCompleteFilter
from adminfilters.mixin import AdminFiltersMixin
from django.contrib import admin
from .models import *
# from admin_auto_filters.filters import AutocompleteFilterFactory


class FosTypeAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'created_at', 'updated_at')
    list_display_links = ('id', 'name')
    search_fields = ['name']


admin.site.register(FosType, FosTypeAdmin)


class FosDocumentAdminInline(admin.StackedInline):
    model = Document
    extra = 0


class FosAdmin(AdminFiltersMixin):
    list_display = ('id', 'name', 'type_text', 'created_at', 'updated_at')
    list_select_related = ('type', )
    list_display_links = ('id', 'name')
    search_fields = ('id', 'name', 'description')
    list_filter = [
        ("type", AutoCompleteFilter),
    ]
    inlines = (FosDocumentAdminInline, )

    def type_text(self, obj):
        return obj.type.name
    type_text.short_description = 'Тип'


admin.site.register(Fos, FosAdmin)
