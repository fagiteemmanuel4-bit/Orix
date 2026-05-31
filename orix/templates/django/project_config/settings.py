SECRET_KEY = '{{ secret_key }}'
DEBUG = True
ALLOWED_HOSTS = []

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    {% if use_auth %}
    'rest_framework',
    'rest_framework.authtoken',
    {% endif %}
]
