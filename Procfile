release: python manage.py migrate
web: gunicorn deminstore.wsgi
worker: celery -A deminstore worker