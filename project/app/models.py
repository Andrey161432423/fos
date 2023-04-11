from django.db import models


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

    class Meta:
        verbose_name = 'Тип ФОСа'
        verbose_name_plural = 'Типы ФОСов'
