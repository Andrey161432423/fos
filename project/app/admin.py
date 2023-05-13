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
    """
        Класс отвечает за логику управления сущностью "учебная группа"
    """
    list_display = ['name', 'course']
    list_display_links = ['name']
    search_fields = ['name']
    list_filter = ['course']


@admin.register(FosType)
class FosTypeAdmin(admin.ModelAdmin):
    """
        Класс отвечает за логику управления сущностью "тип ФОСа"
    """
    list_display = ['name']
    list_display_links = ['name']
    search_fields = ['name']


class FosDocumentAdminInline(admin.StackedInline):
    """
        Класс отвечает за логику управления вложенной сущностью "документ в ФОСе"
    """
    model = Document
    extra = 0

    def has_permissions_to(self, request, obj):
        """
            Описание прав доступа к сущности
        """
        # разрешаем доступ только супер-администратору или если дисциплина ФОСа принадлежит пользователю
        if request.user.is_superuser or not obj:
            return True
        if isinstance(obj, Discipline):
            return obj.users and obj.users.filter(id=request.user.id).exists()
        if isinstance(obj, Fos):
            return obj.discipline.users and obj.discipline.users.filter(id=request.user.id).exists()
        if isinstance(obj, Document):
            return obj.fos.discipline.users and obj.fos.discipline.users.filter(id=request.user.id).exists()
        return True

    def has_change_permission(self, request, obj):
        """
            Может ли пользователь изменять документ в ФОСе
        """
        return self.has_permissions_to(request, obj)

    def has_add_permission(self, request, obj):
        """
            Может ли пользователь добавлять документ в ФОС
        """
        return self.has_permissions_to(request, obj)

    def has_delete_permission(self, request, obj):
        """
            Может ли пользователь удалять документ из ФОСа
        """
        return self.has_permissions_to(request, obj)


class OwnFosListFilter(admin.SimpleListFilter):
    """
        Класс отвечает за логику фильтра, отображающего только ФОСы пользователя
    """
    title = 'Показать только мои ФОСы'
    parameter_name = 'fos_own'

    def lookups(self, request, model_admin):
        """
            Варианты выбора в фильтре
        """
        return [
            (1, 'да')
        ]

    def queryset(self, request, queryset):
        """
            Логика применения фильтра
        """
        if self.value() == '1':
            return queryset.filter(discipline__users__id=request.user.id)
        return queryset


@admin.register(Fos)
class FosAdmin(AdminFiltersMixin, admin.ModelAdmin):
    """
        Класс отвечает за логику управления сущностью "ФОС"
    """
    list_display = ('discipline', 'type_text', 'name', 'files', 'created_at', 'updated_at')
    list_display_links = ['name']
    list_select_related = ('type', 'discipline')

    search_fields = (
        'name', 'description', 'discipline__name'
    )
    inlines = (FosDocumentAdminInline, )

    def type_text(self, obj):
        """
            Добавление поля 'тип' в список таблицы
        """
        return obj.type.name
    type_text.short_description = 'Тип'

    def lookup_allowed(self, lookup, value):
        """
            Разрешение фильтрации по полям связанных сущностей
        """
        return True

    def files(self, obj):
        """
            Логика отображения поля "документы" в таблице
        """
        links = ''
        i = 0
        for doc in Document.objects.filter(fos=obj):
            if doc.path:
                i += 1
                links += ('<a href="'+doc.path.url+'">'+str(i)+'. '+doc.name+'</a></br>')
        if not links:
            return '-'
        return mark_safe(links)
    files.short_description = 'Документы'

    def get_form(self, request, obj=None, **kwargs):
        """
            Отображение формы
        """
        form = super(FosAdmin, self).get_form(request, obj, **kwargs)
        if not request.user.is_superuser and ('discipline' in form.base_fields):
            # позволяем выбрать пользователю только свои дисциплины при добавлении ФОСа
            form.base_fields['discipline'].queryset = Discipline.objects.filter(users__id=request.user.id)
        return form

    def has_permissions_to(self, request, obj=None):
        """
            Описание прав доступа к сущности
        """
        # разрешаем доступ только супер-администратору или если дисциплина ФОСа принадлежит пользователю
        return request.user.is_superuser or \
            (obj and obj.discipline and obj.discipline.users and obj.discipline.users.filter(id=request.user.id))

    def has_change_permission(self, request, obj=None):
        """
            Может ли пользователь изменять ФОС
        """
        return self.has_permissions_to(request, obj)

    def has_delete_permission(self, request, obj=None):
        """
           Может ли пользователь удалять ФОС
        """
        return self.has_permissions_to(request, obj)

    def has_add_permission(self, request, obj=None):
        """
           Может ли пользователь добавлять ФОС
        """
        return True

    def get_list_filter(self, request):
        """
           Описание логики формирования доступного набора фильтров на странице списка
        """
        if not request.user.is_superuser:
            return [OwnFosListFilter, 'discipline', 'type', 'discipline__users', 'discipline__groups']
        return ['discipline', 'type', 'discipline__users', 'discipline__groups']

    def changelist_view(self, request, extra_context=None):
        """
           Описание логики представления списка
        """
        extra_context = {'title': 'Список ФОСов дисциплин'}

        # устанавливаем для обычных пользователей фильтр "только мои ФОСы" по-умолчанию
        if 'HTTP_REFERER' in request.META and not request.user.is_superuser:
            test = request.META['HTTP_REFERER'].split(request.META['PATH_INFO'])
            if test[-1] and not test[-1].startswith('?') and 'fos_own' not in request.GET:
                q = request.GET.copy()
                q['fos_own'] = '1'
                request.GET = q
                request.META['QUERY_STRING'] = request.GET.urlencode()

        return super(FosAdmin, self).changelist_view(request, extra_context=extra_context)


@admin.register(DisciplineType)
class DisciplineTypeAdmin(admin.ModelAdmin):
    """
        Класс отвечает за логику управления сущностью "Тип дисциплины"
    """
    list_display = ['name']
    list_display_links = ['name']
    search_fields = ['name']


class DocumentAdminStackedInline(nested_admin.NestedStackedInline):
    """
        Класс отвечает за логику управления вложенной сущностью "Документ в ФОСе при управлении дисциплиной"
    """
    model = Document
    extra = 0

    def has_permissions_to(self, request, obj):
        """
            Описание прав доступа к сущности
        """
        # разрешаем доступ только супер-администратору или если дисциплина ФОСа принадлежит пользователю
        if request.user.is_superuser or not obj:
            return True
        if isinstance(obj, Discipline):
            return obj.users and obj.users.filter(id=request.user.id)
        if isinstance(obj, Fos):
            return obj.discipline.users and obj.discipline.users.filter(id=request.user.id)
        if isinstance(obj, Document):
            return obj.fos.discipline.users and obj.fos.discipline.users.filter(id=request.user.id)
        return True

    def has_change_permission(self, request, obj):
        """
           Может ли пользователь изменять документ в ФОСе при управлении дисциплиной
        """
        return self.has_permissions_to(request, obj)

    def has_add_permission(self, request, obj):
        """
            Может ли пользователь добавлять документ в ФОС при управлении дисциплиной
        """
        return self.has_permissions_to(request, obj)

    def has_delete_permission(self, request, obj):
        """
            Может ли пользователь удалять документ из ФОСа при управлении дисциплиной
        """
        return self.has_permissions_to(request, obj)


class FosAdminInline(nested_admin.NestedStackedInline):
    """
        Класс отвечает за логику управления вложенной сущностью "ФОС в дисциплине"
    """
    model = Fos
    extra = 0
    inlines = [DocumentAdminStackedInline]

    def has_permissions_to(self, request, obj):
        """
            Описание прав доступа к сущности
        """
        # разрешаем доступ только супер-администратору или если дисциплина ФОСа принадлежит пользователю
        return request.user.is_superuser or (obj and obj.users and obj.users.filter(id=request.user.id))

    def has_change_permission(self, request, obj):
        """
           Может ли пользователь изменять ФОС в дисциплине
        """
        return self.has_permissions_to(request, obj)

    def has_add_permission(self, request, obj):
        """
           Может ли пользователь добавлять ФОС в дисциплину
        """
        return self.has_permissions_to(request, obj)

    def has_delete_permission(self, request, obj):
        """
           Может ли пользователь удалять ФОС из дисциплины
        """
        return self.has_permissions_to(request, obj)


class OwnDisciplineListFilter(admin.SimpleListFilter):
    """
        Класс отвечает за логику фильтра, отображающего только дисциплины пользователя
    """
    title = 'Показать только мои дисциплины'
    parameter_name = 'discipline_own'

    def lookups(self, request, model_admin):
        """
            Варианты выбора в фильтре
        """
        return [
            (1, 'да')
        ]

    def queryset(self, request, queryset):
        """
            Логика применения фильтра
        """
        if self.value() == '1':
            return queryset.filter(users__id=request.user.id)
        return queryset


@admin.register(Discipline)
class DisciplineAdmin(nested_admin.NestedModelAdmin):
    """
        Класс отвечает за логику управления сущностью "Дисциплина"
    """
    list_display_links = ('name', )
    search_fields = ['name', 'type__name', 'fos__document__name', 'fos__name']
    inlines = [FosAdminInline]

    def get_readonly_fields(self, request, obj):
        """
           Описание логики блокировки полей на форме
        """
        # блокируем все поля на форме если пользователь не супер-админ
        if request.user.is_superuser:
            return []
        return ['name', 'type', 'users', 'groups']

    def has_change_permission(self, request, obj=None):
        """
           Может ли пользователь изменять дисциплину
        """
        # разрешаем работу только со своими дисциплинами или если юзер - супер-админ
        return (obj and obj.users and obj.users.filter(id=request.user.id).exists()) or request.user.is_superuser

    def lookup_allowed(self, lookup, value):
        """
            Разрешение фильтрации по полям связанных сущностей
        """
        return True

    def changelist_view(self, request, extra_context=None):
        """
           Описание логики представления списка
        """
        extra_context = {'title': 'Список учебных дисциплин'}

        # устанавливаем для обычных пользователей фильтр "только мои дисциплины" по-умолчанию
        if 'HTTP_REFERER' in request.META and not request.user.is_superuser:
            test = request.META['HTTP_REFERER'].split(request.META['PATH_INFO'])
            if test[-1] and not test[-1].startswith('?') and 'discipline_own' not in request.GET:
                q = request.GET.copy()
                q['discipline_own'] = '1'
                request.GET = q
                request.META['QUERY_STRING'] = request.GET.urlencode()
        return super(DisciplineAdmin, self).changelist_view(request, extra_context=extra_context)

    def get_groups(self, obj):
        return ", ".join([g.name for g in obj.groups.all()])
    get_groups.short_description = 'Группы'

    def get_users(self, obj):
        names = []
        for u in obj.users.all():
            if u.first_name or u.last_name:
                names.append(u.first_name + " " + u.last_name)
            else:
                names.append(u.username)
        return ", ".join(names)
    get_users.short_description = 'Преподаватели'

    def get_list_display(self, request):
        """
            Поля отображаемые в списке
        """
        return ['name', 'type', 'get_users', 'get_groups', 'created_at', 'updated_at']

    def get_list_filter(self, request):
        """
           Описание логики формирования доступного набора фильтров на странице списка
        """
        if not request.user.is_superuser:
            return [OwnDisciplineListFilter, 'type', 'users', 'groups', 'groups__course']
        return ['type', 'users', 'groups', 'groups__course']
