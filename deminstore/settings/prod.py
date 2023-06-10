import os
import dj_database_url

from .common import *

DEBUG = False

SECRET_KEY = os.environ['SECRET_KEY']

ALLOWED_HOSTS = ['deminstore-prod.herokuapp.com']

DATABASES = {
    "default": dj_database_url.config()
}

REDIS_URL = os.environ['REDISCLOUD_URL']

CELERY_BROKER_URL = REDIS_URL

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": REDIS_URL,
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        }
    }
}

# Email settings
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.environ['MAILGUN_SMTP_SERVER']
EMAIL_PORT = os.environ['MAILGUN_SMTP_PORT']
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.environ['MAILGUN_SMTP_LOGIN']
EMAIL_HOST_PASSWORD = os.environ['MAILGUN_SMTP_PASSWORD']
DEFAULT_FROM_EMAIL = os.environ['MAILGUN_SMTP_LOGIN']
