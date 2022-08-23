from .base import *
import ssl


ssl_context = ssl.SSLContext()
ssl_context.check_hostname = False

heroku_redis_ssl_host = {
    'address': os.environ.get('REDIS_TLS_URL'),
    'ssl': ssl_context
}

CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            "hosts": (heroku_redis_ssl_host,),
        }
    },
}

SIMPLE_JWT['AUTH_COOKIE_SECURE'] = True

# MIDDLEWARE.insert(0, 'django.middleware.cache.UpdateCacheMiddleware')
# MIDDLEWARE.append('django.middleware.cache.FetchFromCacheMiddleware')

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

STATICFILES_STORAGE = 'config.storage_backends.StaticStorage'
DEFAULT_FILE_STORAGE = 'config.storage_backends.MediaStorage'

STATIC_ROOT = f'{AWS_URL}{STATIC_URL}'
MEDIA_ROOT = f'{AWS_URL}{MEDIA_URL}'
REMOTE_FILE_STORAGE = True

# CACHES = {
#     'default': {
#         'BACKEND': 'django_redis.cache.RedisCache',
#         'LOCATION': os.environ.get('REDIS_URL'),
#         'OPTIONS': {
#             'CLIENT_CLASS': 'django_redis.client.DefaultClient',
#         }
#     }
# }

DEBUG = True

# CACHE_MIDDLEWARE_SECONDS = 60
