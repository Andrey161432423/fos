from django.db import models
from django.core.validators import FileExtensionValidator, MinValueValidator, MaxValueValidator
from django.conf import settings
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from django.urls import reverse
from django_cleanup import cleanup
import datetime


# валидация размера файла
def validate_file_size(value):
    if value.size > (settings.MAX_UPLOADED_FILE_SIZE * 1024 * 1024):
        raise ValidationError("Максимальный размер загружаемых файлов: " + str(settings.MAX_UPLOADED_FILE_SIZE) + ' Мб')
    else:
        return value


class FosType(models.Model):
    """
    Модель "Тип ФОСа"

    Attributes:
        name: Название
        created_at: Дата создания
        updated_at: дата изменения
    """
    name = models.CharField(max_length=255, verbose_name='Наименование')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата изменения')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Тип оценочного средства'
        verbose_name_plural = 'Типы оценочного средства'


class DisciplineType(models.Model):
    """
    Модель "Тип учебных дисциплин (экзамен, зачет, диф.зачет, ...)"

    Attributes:
        name: Название
        created_at: Дата создания
        updated_at: дата изменения
    """
    name = models.CharField(max_length=255, verbose_name='Наименование')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата изменения')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Тип дисциплины'
        verbose_name_plural = 'Типы дисциплин'


class Group(models.Model):
    """
    Модель "Учебная группа"

    Attributes:
        name: Название
        course: Номер курса
        created_at: Дата создания
        updated_at: дата изменения
    """
    name = models.CharField(max_length=255, verbose_name='Наименование')
    course = models.IntegerField(verbose_name='Курс', default=1, validators=[
        MinValueValidator(1), MaxValueValidator(10)
    ])
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата изменения')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'учебную группу'
        verbose_name_plural = 'Учебные группы'


class Qualification(models.Model):
    """
    Модель "Вид обучения, квалификация (бакалавриат, магистратура, ...)"

    Attributes:
        name: Наименование
    """
    name = models.CharField(max_length=255, verbose_name='Наименование')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'вид обучения'
        verbose_name_plural = 'Виды обучения'


class Discipline(models.Model):
    """
    Модель "Учебная дисциплина"

    Attributes:
        name: Название
        type: Форма контроля знаний
        users: Преподаватели
        groups: Учебные группы
        qualification: Вид обучения
        created_at: Дата создания
        updated_at: дата изменения
    """
    name = models.CharField(max_length=255, verbose_name='Наименование')
    type = models.ForeignKey(DisciplineType, on_delete=models.PROTECT, verbose_name='Форма контроля знаний')
    users = models.ManyToManyField(User, verbose_name='Преподаватели', blank=True)
    groups = models.ManyToManyField(Group, verbose_name='Учебные группы', blank=True)
    qualification = models.ForeignKey(Qualification, blank=True, null=True, on_delete=models.PROTECT,
                                      verbose_name='Вид обучения')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата изменения')

    def __str__(self):
        return self.name

    def get_admin_url(self):
        # the url to the Django admin form for the model instance
        info = (self._meta.app_label, self._meta.model_name)
        return reverse('admin:%s_%s_change' % info, args=(self.pk,))

    class Meta:
        verbose_name = 'Дисциплина'
        verbose_name_plural = 'Дисциплины'


class Fos(models.Model):
    """
        Модель "ФОС (фонд оценочных средств)"

        Attributes:
            name: Название
            description: Описание
            type: Тип ФОСа
            discipline: Дисциплина
            created_at: Дата создания
            updated_at: дата изменения
    """

    YEARS_CHOICES = [
        (str(y), str(y) + " - " + str(y + 1)) for y in reversed(range(2000, datetime.date.today().year + 1))
    ]

    name = models.CharField(max_length=255, verbose_name='Наименование')
    description = models.TextField(verbose_name='Описание', blank=True, null=True)
    type = models.ForeignKey(FosType, on_delete=models.PROTECT, verbose_name='Тип')
    discipline = models.ForeignKey(Discipline, on_delete=models.PROTECT, verbose_name='Дисциплина')
    years = models.CharField(max_length=20, blank=True, null=True, choices=YEARS_CHOICES, verbose_name='Период обучения')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата изменения')

    def __str__(self):
        return 'Оценочное средство - ' + self.name

    class Meta:
        verbose_name = 'оценочное средство'
        verbose_name_plural = 'Оценочные средства'


@cleanup.select
class Document(models.Model):
    """
        Модель "Загружаемый документ"

        Attributes:
            name: Название
            path: Путь до документа на сервере
            fos: ФОС к которому относится данный документ
            created_at: Дата создания
            updated_at: дата изменения
        """
    name = models.CharField(max_length=255, verbose_name='Наименование')
    path = models.FileField(upload_to='documents/', blank=True, null=True, verbose_name='Документ', validators=[
        FileExtensionValidator(settings.ALLOWED_FILE_UPLOAD_EXTENSIONS), validate_file_size
    ], help_text='Допустимые расширения: ' + ', '.join(settings.ALLOWED_FILE_UPLOAD_EXTENSIONS))
    fos = models.ForeignKey(Fos, on_delete=models.CASCADE, verbose_name='Оценочное средство')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата изменения')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Документ'
        verbose_name_plural = 'Документы'