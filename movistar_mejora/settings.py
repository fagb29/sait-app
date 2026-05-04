from pathlib import Path
from decouple import config

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = config('SECRET_KEY', default='django-insecure-aozdlh+@94_k4-mpwhr0pg3#zi92c3b!6pa0-6t$z_=6s6#&(u')
DEBUG = config('DEBUG', default=True, cast=bool)
ALLOWED_HOSTS = config(
    'ALLOWED_HOSTS',
    default='localhost,127.0.0.1,192.168.1.105,.pythonanywhere.com',
    cast=lambda v: [s.strip() for s in v.split(',')]
)


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # App personalizada
    'tecnicos',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',  # Agregado para traducción
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'movistar_mejora.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'tecnicos.context_processors.device_detector',  # Detector de dispositivo móvil
            ],
        },
    },
]

WSGI_APPLICATION = 'movistar_mejora.wsgi.application'


# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

# Configuración de base de datos PostgreSQL
# NOTA: Usando SQLite temporalmente para desarrollo rápido
# Para usar PostgreSQL, comenta la configuración SQLite y descomenta la de PostgreSQL

# SQLite (temporal para desarrollo)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# PostgreSQL (descomentar cuando esté configurado)
# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.postgresql',
#         'NAME': 'movistar_mejora',  # Nombre de la base de datos
#         'USER': 'postgres',  # Usuario de PostgreSQL
#         'PASSWORD': 'tu_password',  # Cambiar por tu contraseña
#         'HOST': 'localhost',  # Servidor de base de datos
#         'PORT': '5432',  # Puerto de PostgreSQL
#     }
# }


# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/

# Idioma español
LANGUAGE_CODE = 'es'  # Cambiado de 'es-cl' a 'es' para mejor compatibilidad

# Zona horaria de Chile
TIME_ZONE = 'America/Santiago'

USE_I18N = True

USE_L10N = True  # Formato de números y fechas en español

USE_TZ = True

# Formatos de fecha en español
DATE_FORMAT = 'd/m/Y'
DATETIME_FORMAT = 'd/m/Y H:i'
SHORT_DATE_FORMAT = 'd/m/Y'


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = []
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ===== CONFIGURACIÓN DE EMAIL =====
# Configuración para envío de emails (usando Gmail como ejemplo)
# Para usar Gmail, debes habilitar "Acceso de apps menos seguras" o usar "Contraseñas de aplicación"
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='tu_email@gmail.com')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='tu_password_de_app')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default=f'SAIT <{EMAIL_HOST_USER}>')
EMAIL_DESTINO = config('EMAIL_DESTINO', default='felipe.g.bravo@gmail.com')


# ===== CONFIGURACIÓN DE LOGIN =====
LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/login/'
