from .base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []

# Database
# https://docs.djangoproject.com/en/3.1/ref/settings/#databases

# En este apartado indicamos la Base de Datos con la que trabajaremos
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        #Si usamos Unipath esta línea debe cambiarse 'NAME': BASE_DIR / 'db.sqlite3'
        'NAME': 'vlandb',
        'USER': 'kevin',
        'PASSWORD': '1234',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
# Le indicamos a Django el directorio de los archivos estáticos
STATICFILES_DIRS = [BASE_DIR.child('static')]


