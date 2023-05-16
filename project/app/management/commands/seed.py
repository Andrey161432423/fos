from django.core.management.base import BaseCommand
from app.models import FosType, DisciplineType, Qualification
from django.contrib.auth.models import Group, Permission


class Command(BaseCommand):

    help = 'Заполнить базу данных тестовыми значениями'

    def handle(self, *args, **kwargs):
        self.stdout.write('Заполнение базы данных значениями по-умолчанию...')

        # если типов ФОСов еще не было в БД - создаем список по-умолчанию
        if FosType.objects.all().count() == 0:
            for fos_type in (
                'Вопросы к зачету / экзамену',
                'Задание для опроса',
                'Тестовое задание',
                'Лабораторное задание',
                'Практическое задание',
                'Расчетные задачи',
                'Реферат',
                'Индивидуальное задание',
                'Курсовой проект'
            ):
                FosType(name=fos_type).save()

        # если типов дисциплин еще не было в БД - создаем список по-умолчанию
        if DisciplineType.objects.all().count() == 0:
            for dis_type in (
                'Зачет',
                'Экзамен',
            ):
                DisciplineType(name=dis_type).save()

        # если видов обучения (квалификаций) еще не было в БД - создаем список по-умолчанию
        if Qualification.objects.all().count() == 0:
            for qualification in (
                'Бакалавриат',
                'Магистратура',
            ):
                Qualification(name=qualification).save()

        # если группы преподаватель не существует - создаем такую и выдаем соответствующие права
        if Group.objects.filter(name='Преподаватель').count() == 0:
            teacher = Group(name='Преподаватель')
            teacher.save()
            for permission in (
                'add_fos', 'change_fos', 'delete_fos', 'view_fos',
                'add_document', 'change_document', 'delete_document', 'view_document',
                'change_discipline', 'view_discipline', 'view_qualification'
            ):
                teacher.permissions.add(
                    Permission.objects.get(codename=permission)
                )
            teacher.save()

        self.stdout.write(
            self.style.SUCCESS('Успешно!')
        )
