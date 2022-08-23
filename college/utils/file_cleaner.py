import os
from typing import Union
from django.conf import settings
import re
from django.db.models.fields.files import ImageFieldFile, FieldFile
from college.utils import aws_supplier
from urllib import parse


def get_file_path(field: Union[ImageFieldFile, FieldFile]):
    try:
        return field.path
    except NotImplementedError:
        url = field.url
        return re.search(f'(media/.*)', url, flags=re.I | re.S).group()


def delete_assigned_file(field: Union[ImageFieldFile, FieldFile]):
    try:
        path = field.path
        if os.path.exists(path):
            os.remove(path)
    # when using remote storage path is not implemented
    except NotImplementedError:
        path = parse.unquote(re.search(f'({settings.MEDIA_URL.lstrip("/")}.*)', field.url, flags=re.I | re.S).group())
        if aws_supplier.check_path(path):
            aws_supplier.delete_file(path)
    # file does not exist
    except ValueError:
        return

