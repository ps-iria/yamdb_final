from datetime import datetime

from django.core.exceptions import ValidationError


def year_validator(value):
    if value < 1500:
        raise ValidationError(
            ('Год издания не может быть меньше или равным "1500". '
             'Введите корректное значение.'),
            params={'value': value},
        )
    if value > datetime.now().year:
        raise ValidationError(
            ('Год издания не может быть больше текущего. '
             'Введите корректное значение.'),
            params={'value': value},
        )
