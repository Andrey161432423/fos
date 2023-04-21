from django.core.management.base import BaseCommand
from app.models import FosType, DisciplineType
from django.contrib.auth.models import Group, Permission


class Command(BaseCommand):

    help = 'Заполнить базу данных тестовыми значениями'

    def handle(self, *args, **kwargs):
        self.stdout.write('Заполнение базы данных значениями по-умолчанию...')

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

        if DisciplineType.objects.all().count() == 0:
            for dis_type in (
                'Зачет',
                'Экзамен',
            ):
                DisciplineType(name=dis_type).save()

        if Group.objects.filter(name='Преподаватель').count() == 0:
            teacher = Group(name='Преподаватель')
            teacher.save()
            for permission in (
                'add_fos', 'change_fos', 'delete_fos', 'view_fos',
                'add_document', 'change_document', 'delete_document', 'view_document',
                'add_discipline', 'change_discipline', 'delete_discipline', 'view_discipline',
            ):
                teacher.permissions.add(
                    Permission.objects.get(codename=permission)
                )
            teacher.save()

        self.stdout.write(
            self.style.SUCCESS('Успешно!')
        )
