import os

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'secret_key'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []

CACHE_MIDDLEWARE_SECONDS = 600

USE_ETAGS = True

INSTALLED_APPS = [
    'djangocache',
]

MIDDLEWARE_CLASSES = []


# Internationalization
# https://docs.djangoproject.com/en/1.9/topics/i18n/

TIME_ZONE = 'UTC'

USE_TZ = True
