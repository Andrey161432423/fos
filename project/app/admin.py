from adminfilters.mixin import AdminFiltersMixin
from django.contrib import admin
from .models import *
import nested_admin
from django.utils.html import mark_safe, format_html
from django.urls import reverse
from django.utils.http import urlencode
from .utils import ru_plural
from import_export.admin import ImportExportModelAdmin
from import_export.fields import Field
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin
from import_export.admin import ExportMixin, ImportMixin, ExportActionMixin
from django.contrib.auth.models import Group as UserGroup
from import_export import fields, resources
from import_export.widgets import ForeignKeyWidget, ManyToManyWidget

admin.site.site_header = 'Цифровой фонд оценочных средств'
admin.site.index_title = 'Главное меню'
admin.site.site_title = 'Цифровой фонд оценочных средств'

User.get_short_name = lambda user_instance: (user_instance.last_name + " " + user_instance.first_name) \
    if user_instance.last_name or user_instance.first_name else user_instance.username


class UserResource(resources.ModelResource):
    """
       Класс описывает логику импорта сущности "пользователь"
    """
    class Meta:
        model = User
        import_id_fields = ('username',)
        fields = ('username', 'first_name', 'last_name')

    def after_save_instance(self, instance, using_transactions, dry_run):
        """
            Событие "после сохранения"
        """
        # выставляем статус персонала и группу "преподаватели" по-умолчанию
        instance.is_staff = True
        instance.groups.add(
            UserGroup.objects.first()
        )
        instance.save()


# переопределяем django-класс админской сущности "пользователь"
class CustomUserAdmin(ImportMixin, UserAdmin):
    resource_class = UserResource
    pass


admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)


class GroupImportResource(resources.ModelResource):
    """
       Класс описывает логику импорта сущности "учебная группа"
    """
    class Meta:
        model = Group
        import_id_fields = ('name', )
        fields = ('name', 'course')


class GroupExportResource(resources.ModelResource):
    """
       Класс описывает логику экспорта сущности "учебная группа"
    """
    id_custom = Field(attribute='id', column_name='ID')
    name_custom = Field(attribute='name', column_name='Наименование')
    course_custom = Field(attribute='course', column_name='Курс')

    class Meta:
        model = Group
        fields = ('id_custom', 'name_custom', 'course_custom')


@admin.register(Group)
class GroupAdmin(ImportExportModelAdmin):
    """
        Класс отвечает за логику управления сущностью "учебная группа"
    """
    list_display = ['name', 'course', 'view_disciplines_link']
    list_display_links = ['name']
    search_fields = ['name']
    list_filter = ['course']
    resource_classes = [GroupImportResource]

    def get_export_resource_class(self):
        return GroupExportResource

    def view_disciplines_link(self, obj):
        """
            Логика отображения колонки для перехода в список дисциплин группы
        """
        count = obj.discipline_set.count()
        url = (
                reverse("admin:app_discipline_changelist")
                + "?"
                + urlencode({"groups__id__exact": f"{obj.id}"})
        )
        return format_html('<a href="{}">Просмотр <b>({})</b></a>', url, count)
    view_disciplines_link.short_description = "Дисциплины"


@admin.register(Qualification)
class QualificationAdmin(admin.ModelAdmin):
    """
        Класс отвечает за логику управления сущностью "вид обучения, квалификация"
    """
    search_fields = ['name']

    def get_queryset(self, request):
        # добавляем объект request в объект self, для доступа к нему из любой функции данного класса
        qs = super(QualificationAdmin, self).get_queryset(request)
        self.request = request
        return qs

    def get_list_display(self, request):
        """
            Поля отображаемые в списке
        """
        if request.user.is_superuser:
            return ['name', 'view_disciplines_link_admin']
        return ['view_disciplines_link']

    def view_disciplines_link(self, obj):
        """
            Логика отображения страницы списка квалификаций для преподавателей
        """
        total = obj.discipline_set.count()
        own = obj.discipline_set.filter(users__id=self.request.user.id).count()
        url = (
                reverse("admin:app_discipline_changelist")
                + "?"
                + urlencode({"qualification__id__exact": f"{obj.id}"})
        )
        # выводим в одну колонку название квалификации, количество дисциплин закрепленных за преподавателем
        # и общее кол-во дисциплин этого вида обучения
        # например: "Бакалавриат (3 дисциплины) всего 10"
        return format_html('<a href="{}">'+obj.name+' ({} '+ru_plural(own, ["дисциплина", "дисциплины", "дисциплин"])
                           + ')</a> <i>всего: {}</i>', url, own, total)
    view_disciplines_link.short_description = "Вид обучения"

    def view_disciplines_link_admin(self, obj):
        """
            Логика отображения страницы списка квалификаций для администратора
        """
        count = obj.discipline_set.count()
        url = (
                reverse("admin:app_discipline_changelist")
                + "?"
                + urlencode({"qualification__id__exact": f"{obj.id}"})
        )
        # выводим 2 колонки: название квалификации и ссылку на страницу со списком квалификаций
        # например: "Бакалавриат - Перейти (3)"
        return format_html('<a href="{}">Перейти ({})</a>', url, count)
    view_disciplines_link_admin.short_description = "Дисциплины"


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
    title = 'Показать только мои оценочные средства'
    parameter_name = 'fos_own'

    def lookups(self, request, model_admin):
        """
            Варианты выбора в фильтре
        """
        return [
            (1, 'Да')
        ]

    def queryset(self, request, queryset):
        """
            Логика применения фильтра
        """
        if self.value() == '1':
            return queryset.filter(discipline__users__id=request.user.id)
        return queryset


class DisTeachersListFilter(admin.SimpleListFilter):
    """
        Класс отвечает за логику фильтра "преподаватель через дисциплину"
    """
    title = "Преподаватель"
    parameter_name = 'teacher'

    def lookups(self, request, model_admin):
        """
            Варианты выбора в фильтре
        """
        users = []
        for u in User.objects.all():
            name = u.last_name + " " + u.first_name if u.last_name or u.first_name else u.username
            users.append((u.id, name))
        return users

    def queryset(self, request, queryset):
        """
            Логика применения фильтра
        """
        if not self.value():
            return queryset
        return queryset.filter(discipline__users__id=self.value())


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
            return [OwnFosListFilter, 'years', 'discipline', 'type', DisTeachersListFilter, 'discipline__groups']
        return ['years', 'discipline', 'type', DisTeachersListFilter, 'discipline__groups']

    def changelist_view(self, request, extra_context=None):
        """
           Описание логики представления списка
        """

        # устанавливаем для обычных пользователей фильтр "только мои ФОСы" по-умолчанию
        if 'HTTP_REFERER' in request.META and not request.user.is_superuser:
            test = request.META['HTTP_REFERER'].split(request.META['PATH_INFO'])
            if test[-1] and not test[-1].startswith('?') and 'fos_own' not in request.GET:
                q = request.GET.copy()
                q['fos_own'] = '1'
                request.GET = q
                request.META['QUERY_STRING'] = request.GET.urlencode()

        title = 'Список оценочных средств дисциплин'
        if 'discipline__id__exact' in request.GET:
            discipline = Discipline.objects.get(pk=request.GET['discipline__id__exact'])
            title = discipline.name + ': ФОСы'
        if 'type__id__exact' in request.GET:
            fos_type = FosType.objects.get(pk=request.GET['type__id__exact'])
            title = title + " (" + fos_type.name.lower() + ")"

        if 'teacher' in request.GET or ('fos_own' in request.GET and request.GET['fos_own'] == 1):
            if 'fos_own' in request.GET and request.GET['fos_own'] == 1:
                user = request.user
            else:
                user = User.objects.get(pk=request.GET['teacher'])
            if user.first_name or user.last_name:
                username = user.first_name + " " + user.last_name
            else:
                username = user.username
            title = "("+username+") " + title
        elif 'discipline__groups__id__exact' in request.GET:
            group = Group.objects.get(pk=request.GET['discipline__groups__id__exact'])
            title = "(" + group.name.upper() + ") " + title

        extra_context = {'title': title}

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


class TeachersListFilter(admin.SimpleListFilter):
    """
        Класс отвечает за логику фильтра "преподаватель"
    """
    title = "Преподаватель"
    parameter_name = 'teacher'

    def lookups(self, request, model_admin):
        """
            Варианты выбора в фильтре
        """
        users = []
        for u in User.objects.all():
            name = u.last_name + " " + u.first_name if u.last_name or u.first_name else u.username
            users.append((u.id, name))
        return users

    def queryset(self, request, queryset):
        """
            Логика применения фильтра
        """
        if not self.value():
            return queryset
        return queryset.filter(users__id=self.value())


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
            (1, 'Да')
        ]

    def queryset(self, request, queryset):
        """
            Логика применения фильтра
        """
        if self.value() == '1':
            return queryset.filter(users__id=request.user.id)
        return queryset


class DisciplineImportResource(resources.ModelResource):
    """
       Класс описывает логику импорта сущности "дисциплина"
    """
    name = Field(attribute='name', column_name='name')
    type = fields.Field(
        column_name='type', attribute='type',
        widget=ForeignKeyWidget(DisciplineType, field='name')
    )
    qualification = fields.Field(
        column_name='qualification', attribute='qualification',
        widget=ForeignKeyWidget(Qualification, field='name')
    )
    users = fields.Field(
        column_name='users', attribute='users',
        widget=ManyToManyWidget(User, field='username', separator='|')
    )
    groups = fields.Field(
        column_name='groups', attribute='groups',
        widget=ManyToManyWidget(Group, field='name', separator='|')
    )

    class Meta:
        model = Discipline
        import_id_fields = ('name', )
        fields = ('name', 'type', 'qualification', 'groups', 'users')


class DisciplineExportResource(resources.ModelResource):
    """
       Класс описывает логику экспорта сущности "дисциплина"
    """
    name = Field(attribute='name', column_name='Дисциплина')
    type = Field(attribute='type', column_name='Форма контроля знаний')
    qualification = Field(attribute='qualification', column_name='Вид обучения')
    users = Field(attribute='users', column_name='Преподаватель', widget=ManyToManyWidget(
        User, field='username', separator=', '), default='-'
    )
    groups = Field(attribute='groups', column_name='Учебные группы', widget=ManyToManyWidget(
        Group, field='name', separator=', '), default='-'
    )
    foses = Field(attribute='fos_set', column_name='Оценочные средства', widget=ManyToManyWidget(
        Fos, field='name', separator=', '), default='-'
    )

    class Meta:
        model = Discipline
        fields = ('name', 'type', 'users', 'groups', 'foses')

    def dehydrate_users(self, discipline):
        out = []
        for user in discipline.users.all():
            if user.first_name or user.last_name:
                out.append(user.first_name + " " + user.last_name)
            else:
                out.append(user.username)
        return ", ".join(out)


@admin.register(Discipline)
class DisciplineAdmin(ImportExportModelAdmin, ExportActionMixin, nested_admin.NestedModelAdmin):
    """
        Класс отвечает за логику управления сущностью "Дисциплина"
    """
    list_display_links = ('name', )
    search_fields = ['name', 'type__name', 'qualification__name', 'fos__document__name', 'fos__name']
    inlines = [FosAdminInline]
    resource_classes = [DisciplineImportResource]
    save_on_top = True

    def get_export_resource_class(self):
        return DisciplineExportResource

    def view_foses_link(self, obj):
        """
            Логика отображения колонки для перехода в список ФОСов
        """
        count = obj.fos_set.count()
        if self.request.user.is_superuser:
            url = (reverse("admin:app_fos_changelist") + "?" + urlencode({"discipline__id__exact": f"{obj.id}"}))
        else:
            url = (reverse("admin:app_fos_changelist") + "?" + urlencode({"discipline__id__exact": f"{obj.id}", "fos_own": 0}))
        return format_html('<a href="{}">Просмотр <b>({})</b></a>', url, count)
    view_foses_link.short_description = "ФОСы"

    def get_readonly_fields(self, request, obj):
        """
           Описание логики блокировки полей на форме
        """
        # блокируем все поля на форме если пользователь не супер-админ
        if request.user.is_superuser:
            return []
        return ['name', 'type', 'qualification', 'users', 'groups']

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

        # устанавливаем для обычных пользователей фильтр "только мои дисциплины" по-умолчанию
        if 'HTTP_REFERER' in request.META and not request.user.is_superuser:
            test = request.META['HTTP_REFERER'].split(request.META['PATH_INFO'])
            if test[-1] and not test[-1].startswith('?') and 'discipline_own' not in request.GET:
                q = request.GET.copy()
                q['discipline_own'] = '1'
                request.GET = q
                request.META['QUERY_STRING'] = request.GET.urlencode()

        title = 'Список учебных дисциплин'
        if 'qualification__id__exact' in request.GET:
            qualification = Qualification.objects.get(pk=request.GET['qualification__id__exact'])
            title = "(" + qualification.name + ") " + title
        if 'teacher' in request.GET or ('discipline_own' in request.GET and request.GET['discipline_own'] == 1):
            if 'discipline_own' in request.GET:
                user = request.user
            else:
                user = User.objects.get(pk=request.GET['teacher'])
            if user.first_name or user.last_name:
                username = user.first_name + " " + user.last_name
            else:
                username = user.username
            title = title + " преподавателя " + username.lower()
        elif 'groups__id__exact' in request.GET:
            group = Group.objects.get(pk=request.GET['groups__id__exact'])
            title = title + " группы " + group.name.upper()

        extra_context = {'title': title}

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
        return ['name', 'type', 'qualification', 'get_users', 'get_groups', 'view_foses_link', 'created_at', 'updated_at']

    def get_list_filter(self, request):
        """
           Описание логики формирования доступного набора фильтров на странице списка
        """
        if not request.user.is_superuser:
            return [OwnDisciplineListFilter, 'qualification', 'type', TeachersListFilter, 'groups', 'groups__course']
        return ['qualification', 'type', TeachersListFilter, 'groups', 'groups__course']

    def get_queryset(self, request):
        # добавляем объект request в объект self, для доступа к нему из любой функции данного класса
        qs = super(DisciplineAdmin, self).get_queryset(request)
        self.request = request
        return qs
