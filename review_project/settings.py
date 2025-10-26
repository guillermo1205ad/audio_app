"""
Django settings for review_project (Audio Review App)
Adaptado para portabilidad y seguridad.
"""

from pathlib import Path
from django.urls import reverse_lazy
import os

# ==============================================================
# 📁 BASE DIRECTORY
# ==============================================================

BASE_DIR = Path(__file__).resolve().parent.parent


# ==============================================================
# 🔐 SECURITY
# ==============================================================

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "dev-secret-key")
DEBUG = os.getenv("DJANGO_DEBUG", "True").lower() == "true"
ALLOWED_HOSTS = os.getenv("DJANGO_ALLOWED_HOSTS", "127.0.0.1,localhost").split(",")


# ==============================================================
# 🧩 INSTALLED APPS
# ==============================================================

INSTALLED_APPS = [
    # Core Django
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Autenticación (django-allauth)
    'django.contrib.sites',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',

    # App local
    'review',
]


# ==============================================================
# ⚙️ MIDDLEWARE
# ==============================================================

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'allauth.account.middleware.AccountMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]


# ==============================================================
# 🌐 ROOT CONFIGURATION
# ==============================================================

ROOT_URLCONF = 'review_project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],  # Plantillas globales
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'review_project.wsgi.application'


# ==============================================================
# 🗄️ DATABASE (PostgreSQL)
# ==============================================================

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv("DB_NAME", "plataforma_revision"),
        'USER': os.getenv("DB_USER", "audio_user"),
        'PASSWORD': os.getenv("DB_PASSWORD", "audios_2025"),
        'HOST': os.getenv("DB_HOST", "localhost"),
        'PORT': os.getenv("DB_PORT", "5432"),
    }
}


# ==============================================================
# 🔑 PASSWORD VALIDATION
# ==============================================================

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]


# ==============================================================
# 🌍 INTERNATIONALIZATION
# ==============================================================

LANGUAGE_CODE = 'en-us'
TIME_ZONE = os.getenv("DJANGO_TIMEZONE", "UTC")
USE_I18N = True
USE_TZ = True


# ==============================================================
# 🧾 STATIC & MEDIA FILES
# ==============================================================

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/'
MEDIA_ROOT = os.getenv("MEDIA_ROOT", str(BASE_DIR / 'media'))


# ==============================================================
# 🧱 DEFAULT AUTO FIELD
# ==============================================================

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# ==============================================================
# 👥 AUTHENTICATION (AllAuth)
# ==============================================================

SITE_ID = 1

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

LOGIN_URL = reverse_lazy('account_login')
LOGIN_REDIRECT_URL = reverse_lazy('review:pending_list')
ACCOUNT_LOGOUT_REDIRECT_URL = reverse_lazy('account_login')

ACCOUNT_EMAIL_VERIFICATION = 'none'
ACCOUNT_LOGIN_METHODS = {'username'}
ACCOUNT_LOGIN_ON_EMAIL_CONFIRMATION = True
ACCOUNT_SIGNUP_FIELDS = ['email', 'username', 'password1', 'password2']


# ==============================================================
# 🌐 SOCIAL AUTH (Google OAuth)
# ==============================================================

SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'APP': {
            'client_id': os.getenv("GOOGLE_CLIENT_ID", ""),
            'secret': os.getenv("GOOGLE_CLIENT_SECRET", ""),
            'key': '',
        },
        'SCOPE': ['profile', 'email'],
        'AUTH_PARAMS': {'access_type': 'online'},
    }
}


# ==============================================================
# ✉️ EMAIL (SMTP)
# ==============================================================

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.getenv("EMAIL_HOST", "smtp.gmail.com")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", 587))
EMAIL_USE_TLS = os.getenv("EMAIL_USE_TLS", "True").lower() == "true"
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "")
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER or "no-reply@example.com"


# ==============================================================
# 🧩 LOCAL SETTINGS (opcional)
# ==============================================================

try:
    from .local_settings import *
except ImportError:
    pass