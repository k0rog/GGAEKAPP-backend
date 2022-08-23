import re
import jwt
from django.conf import settings


def parse_query_sting(query_string):
    query_string = query_string.decode('utf-8')

    query_list = re.split('[&=]', query_string)

    kwargs = {query_list[i]: query_list[i + 1] for i in range(0, len(query_list), 2)}

    return kwargs['access']


def check_token(query_string):
    token = parse_query_sting(query_string)

    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
    except Exception as e:
        return False
