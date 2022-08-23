from django.core.exceptions import ValidationError
from datetime import datetime
from django.utils.translation import gettext_lazy as _


def validate_start_year(value):
    current_year = datetime.now().year

    if current_year - 6 <= value <= current_year + 1:
        return value
    else:
        raise ValidationError(_(f'Enter a valid year between {current_year-6} and {current_year+1}'))


def validate_group_number(value):
    if 1 <= value <= 5:
        return value
    else:
        raise ValidationError(_(f'Enter a valid group number between 1 and 5'))
