from adminfilters.autocomplete import AutoCompleteFilter
from adminfilters.mixin import AdminFiltersMixin
from django.contrib import admin
from .models import *
import nested_admin

admin.site.site_header = 'Цифровой фонд оценочных средств'
admin.site.index_title = 'Администрирование'
admin.site.site_title = 'Цифровой фонд оценочных средств'


@admin.register(FosType)
class FosTypeAdmin(admin.ModelAdmin):
    list_display = ['name']
    list_display_links = ['name']
    search_fields = ['name']


class FosDocumentAdminInline(admin.StackedInline):
    model = Document
    extra = 0


@admin.register(Fos)
class FosAdmin(AdminFiltersMixin, admin.ModelAdmin):
    list_display = ('name', 'type_text', 'discipline', 'created_at', 'updated_at')
    list_select_related = ('type', 'discipline')

    search_fields = (
        'name', 'description', 'discipline__name', 'discipline__fos__document__name', 'discipline__fos__name'
    )
    list_filter = [
        ("discipline", AutoCompleteFilter), 'type'
    ]
    inlines = (FosDocumentAdminInline, )

    def type_text(self, obj):
        return obj.type.name
    type_text.short_description = 'Тип'

    def get_form(self, request, obj=None, **kwargs):
        form = super(FosAdmin, self).get_form(request, obj, **kwargs)
        if not request.user.is_superuser:
            form.base_fields['discipline'].queryset = Discipline.objects.filter(user=request.user)
        return form

    def get_queryset(self, request):
        qs = super(FosAdmin, self).get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(discipline__user=request.user)

    def changelist_view(self, request, extra_context=None):
        extra_context = {'title': 'Список ФОСов дисциплин'}
        return super(FosAdmin, self).changelist_view(request, extra_context=extra_context)


@admin.register(DisciplineType)
class DisciplineTypeAdmin(admin.ModelAdmin):
    list_display = ['name']
    list_display_links = ['name']
    search_fields = ['name']


class DocumentAdminStackedInline(nested_admin.NestedStackedInline):
    model = Document
    extra = 0


class FosAdminInline(nested_admin.NestedStackedInline):
    model = Fos
    extra = 0
    inlines = [DocumentAdminStackedInline]


@admin.register(Discipline)
class DisciplineAdmin(nested_admin.NestedModelAdmin):
    list_display = ('name', 'type', 'created_at', 'updated_at')
    list_display_links = ('name', )
    exclude = ['user']
    search_fields = ['name', 'fos__document__name', 'fos__name']
    inlines = [FosAdminInline]
    list_filter = ['type']

    def save_model(self, request, obj, form, change):
        obj.user = request.user
        obj.save()

    def get_queryset(self, request):
        qs = super(DisciplineAdmin, self).get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(user=request.user)

    def changelist_view(self, request, extra_context=None):
        extra_context = {'title': 'Список учебных дисциплин'}
        return super(DisciplineAdmin, self).changelist_view(request, extra_context=extra_context)
