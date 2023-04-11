from django.apps import AppConfig


class AppConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    default_charset = 'utf-8'
    name = "app"
    verbose_name = 'Фонды оценочных средств'
