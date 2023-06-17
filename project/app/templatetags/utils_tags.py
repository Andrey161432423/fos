from django import template
from django.contrib.auth.models import User

from app.models import Fos

register = template.Library()


@register.filter
def ru_plural(value, variants):
    variants = variants.split(",")
    value = abs(int(value))

    if value % 10 == 1 and value % 100 != 11:
        variant = 0
    elif value % 10 >= 2 and value % 10 <= 4 and \
            (value % 100 < 10 or value % 100 >= 20):
        variant = 1
    else:
        variant = 2

    return str(value) + " " + variants[variant]


@register.simple_tag
def get_users():
    return User.objects.all()


@register.simple_tag
def get_years():
    return Fos.YEARS_CHOICES
