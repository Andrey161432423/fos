from django.core.management.base import BaseCommand
from app.models import FosType


class Command(BaseCommand):

    help = 'Заполнить базу данных тестовыми значениями'

    def handle(self, *args, **kwargs):
        self.stdout.write('Заполнение базы данных значениями по-умолчанию...')

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

        self.stdout.write(
            self.style.SUCCESS('Успешно!')
        )
