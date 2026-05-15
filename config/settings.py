from pathlib import Path
import os
import sys

BASE_DIR = Path(__file__).resolve().parent.parent
IS_TEST = 'test' in sys.argv
IS_RUNSERVER = 'runserver' in sys.argv

SECRET_KEY = os.environ.get(
    'DJANGO_SECRET_KEY',
    'L8Vr7m4N2pQ9xY1sK6aD3fH0uJ5cT8wZrE2bG7nM4qP9yX1kV6s',
)

DEBUG = os.environ.get('DJANGO_DEBUG', 'True').lower() in {'1', 'true', 'yes', 'on'}

ALLOWED_HOSTS = [
    host.strip()
    for host in os.environ.get('DJANGO_ALLOWED_HOSTS', '*').split(',')
    if host.strip()
]

INSTALLED_APPS = [
    'jazzmin',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'crispy_forms',
    'crispy_bootstrap5',
    'tournament',
    'betting',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'tournament.context_processors.active_tournament',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'fr-fr'
TIME_ZONE = 'Africa/Porto-Novo'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

LOGIN_URL = '/admin/login/'
LOGIN_REDIRECT_URL = '/admin-panel/'

if DEBUG or IS_RUNSERVER:
    SECURE_SSL_REDIRECT = False
    SESSION_COOKIE_SECURE = False
    CSRF_COOKIE_SECURE = False

if not DEBUG and not IS_RUNSERVER:
    SECURE_HSTS_SECONDS = int(os.environ.get('DJANGO_SECURE_HSTS_SECONDS', '31536000'))
    SECURE_HSTS_INCLUDE_SUBDOMAINS = os.environ.get(
        'DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS',
        'True',
    ).lower() in {'1', 'true', 'yes', 'on'}
    SECURE_HSTS_PRELOAD = os.environ.get(
        'DJANGO_SECURE_HSTS_PRELOAD',
        'True',
    ).lower() in {'1', 'true', 'yes', 'on'}
    SECURE_SSL_REDIRECT = not IS_TEST and os.environ.get(
        'DJANGO_SECURE_SSL_REDIRECT',
        'True',
    ).lower() in {
        '1',
        'true',
        'yes',
        'on',
    }
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

JAZZMIN_SETTINGS = {
    "site_title": "ADEIB Admin",
    "site_header": "ADEIB U26",
    "site_brand": "ADEIB U26",
    "welcome_sign": "Bienvenue sur le panneau d'administration",
    "copyright": "ADEIB",
    "search_model": "auth.User",
    "topmenu_links": [
        {"name": "Site", "url": "/", "new_window": False},
        {"name": "Admin panel", "url": "/admin-panel/", "new_window": False},
    ],
    "navigation_expanded": True,
    "hide_apps": [],
    "hide_models": [],
    "order_with_respect_to": [
        "tournament",
        "betting",
        "auth",
    ],
    "icons": {
        "auth": "fas fa-users-cog",
        "auth.user": "fas fa-user",
        "auth.group": "fas fa-users",
        "tournament": "fas fa-trophy",
        "tournament.tournament": "fas fa-flag-checkered",
        "tournament.team": "fas fa-users",
        "tournament.player": "fas fa-user-friends",
        "tournament.match": "fas fa-futbol",
        "tournament.goal": "fas fa-bullseye",
        "tournament.standing": "fas fa-table",
        "tournament.knockoutmatch": "fas fa-sitemap",
        "betting": "fas fa-coins",
        "betting.prediction": "fas fa-check-double",
        "betting.predictionleaderboard": "fas fa-medal",
    },
}
