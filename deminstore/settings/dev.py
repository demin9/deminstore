from .common import *


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
