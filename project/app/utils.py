# функция для склонения множественного числа существительных
def ru_plural(value, variants):
    """
        value = 1, variants = ["час","часа","часов"] => 1 час
        value = 25, variants = ["минуту","минуты","минут"] => 25 минут
    """
    value = abs(int(value))

    if value % 10 == 1 and value % 100 != 11:
        variant = 0
    elif value % 10 >= 2 and value % 10 <= 4 and \
            (value % 100 < 10 or value % 100 >= 20):
        variant = 1
    else:
        variant = 2

    return variants[variant]
