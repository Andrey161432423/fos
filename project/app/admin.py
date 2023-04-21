from adminfilters.autocomplete import AutoCompleteFilter
from adminfilters.mixin import AdminFiltersMixin
from django.contrib import admin
from .models import *
import nested_admin
from django.utils.html import mark_safe

admin.site.site_header = 'Цифровой фонд оценочных средств'
admin.site.index_title = 'Администрирование'
admin.site.site_title = 'Цифровой фонд оценочных средств'


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ['name', 'course']
    list_display_links = ['name']
    search_fields = ['name', 'disciplines__name']
    list_filter = ['course', 'disciplines']
    filter_horizontal = ['disciplines']


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
    list_display = ('discipline', 'type_text', 'name', 'files', 'created_at', 'updated_at')
    list_display_links = ['name']
    list_select_related = ('type', 'discipline')

    search_fields = (
        'name', 'description', 'discipline__name', 'discipline__fos__document__name', 'discipline__fos__name'
    )
    list_filter = [
        # ("discipline", AutoCompleteFilter),
        'discipline', 'discipline__group', 'type',
    ]
    inlines = (FosDocumentAdminInline, )

    def type_text(self, obj):
        return obj.type.name
    type_text.short_description = 'Тип'

    def files(self, obj):
        links = ''
        i = 0
        for doc in Document.objects.filter(fos=obj):
            i += 1
            links += ('<a href="'+doc.path.url+'">'+str(i)+'. '+doc.name+'</a></br>')
        if not links:
            return '-'
        return mark_safe(links)
    files.short_description = 'Документы'

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
    search_fields = ['name', 'type__name', 'fos__document__name', 'fos__name']
    inlines = [FosAdminInline]
    list_filter = ['type']

    def save_model(self, request, obj, form, change):
        if not request.user.is_superuser:
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

    def get_form(self, request, obj=None, **kwargs):
        if not request.user.is_superuser:
            self.exclude = ['user']

        return super(DisciplineAdmin, self).get_form(request, obj, **kwargs)

    def get_list_display(self, request):
        if request.user.is_superuser:
            return ('name', 'type', 'user', 'created_at', 'updated_at')
        return ('name', 'type', 'created_at', 'updated_at')

    def get_list_filter(self, request):
        if request.user.is_superuser:
            return ('type', 'user', 'group')
        return ('type', 'group')
