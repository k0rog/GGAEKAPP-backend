from .base import *


DEBUG = True

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': os.environ.get('ELEPHANT_NAME'),
        'USER': os.environ.get('ELEPHANT_USER'),
        'PASSWORD': os.environ.get('ELEPHANT_PASSWORD'),
        'HOST': os.environ.get('ELEPHANT_HOST'),
        'PORT': 5432
    }
}

CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            "hosts": [os.environ.get('REDIS_URL')],
        }
    },
}

STATICFILES_STORAGE = 'config.storage_backends.StaticStorage'
DEFAULT_FILE_STORAGE = 'config.storage_backends.MediaStorage'

STATIC_ROOT = f'{AWS_URL}{STATIC_URL}'
MEDIA_ROOT = f'{AWS_URL}{MEDIA_URL}'
REMOTE_FILE_STORAGE = True
