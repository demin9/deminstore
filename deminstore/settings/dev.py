import os
from .common import *


SECRET_KEY = os.getenv('SECRET_KEY')

DEBUG = True

#     MIDDLEWARE += ['silk.middleware.SilkyMiddleware']

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": "deminstore",
        "HOST": "localhost",
        "USER": os.getenv('DB_USER'),
        "PASSWORD": os.getenv('DB_PASSWORD')
    }
}

CELERY_BROKER_URL = 'redis://localhost:6379/1'

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://127.0.0.1:6379/2",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        }
    }
}

# Email settings
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL')
