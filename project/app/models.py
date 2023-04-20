from django.db import models
from django.core.validators import FileExtensionValidator
from django.conf import settings
from django.core.exceptions import ValidationError


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
        verbose_name = 'Тип ФОСа'
        verbose_name_plural = 'Типы ФОСов'


class Fos(models.Model):
    """
        Модель "ФОС (фонд оценочных средств)"

        Attributes:
            name: Название
            description: Описание
            type: Тип ФОСа
            created_at: Дата создания
            updated_at: дата изменения
        """
    name = models.CharField(max_length=255, verbose_name='Наименование')
    description = models.TextField(verbose_name='Описание', blank=True, null=True)
    type = models.ForeignKey(FosType, on_delete=models.PROTECT, verbose_name='Тип')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата изменения')

    def __str__(self):
        return 'ФОС - ' + self.name

    class Meta:
        verbose_name = 'ФОС'
        verbose_name_plural = 'ФОСы'


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
    fos = models.ForeignKey(Fos, on_delete=models.PROTECT, verbose_name='ФОС')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата изменения')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Документ'
        verbose_name_plural = 'Документы'


