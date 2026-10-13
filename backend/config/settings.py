import os
from pathlib import Path
from urllib.parse import urlparse, unquote, parse_qsl
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / '.env')
DEBUG = os.getenv('DJANGO_DEBUG', 'false').lower() == 'true'
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'development-only-change-before-hosting')
if not DEBUG and SECRET_KEY == 'development-only-change-before-hosting' and 'test' not in __import__('sys').argv:
    from django.core.exceptions import ImproperlyConfigured
    raise ImproperlyConfigured('Set DJANGO_SECRET_KEY in backend/.env (see .env.example).')
ALLOWED_HOSTS = os.getenv('DJANGO_ALLOWED_HOSTS', 'localhost,127.0.0.1,testserver,.vercel.app').split(',')
INSTALLED_APPS = ['django.contrib.admin', 'django.contrib.auth', 'django.contrib.contenttypes', 'django.contrib.sessions', 'django.contrib.messages', 'django.contrib.staticfiles', 'rest_framework', 'learning']
MIDDLEWARE = ['django.middleware.security.SecurityMiddleware', 'django.contrib.sessions.middleware.SessionMiddleware', 'django.middleware.common.CommonMiddleware', 'django.middleware.csrf.CsrfViewMiddleware', 'django.contrib.auth.middleware.AuthenticationMiddleware', 'django.contrib.messages.middleware.MessageMiddleware', 'django.middleware.clickjacking.XFrameOptionsMiddleware']
# Production serves collected static files from Vercel's CDN; WhiteNoise is a fallback for Django admin assets.
if not DEBUG:
    MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')
ROOT_URLCONF = 'config.urls'
TEMPLATES = [{'BACKEND': 'django.template.backends.django.DjangoTemplates', 'DIRS': [], 'APP_DIRS': True, 'OPTIONS': {'context_processors': ['django.template.context_processors.request', 'django.contrib.auth.context_processors.auth', 'django.contrib.messages.context_processors.messages']}}]
WSGI_APPLICATION = 'config.wsgi.application'
url = urlparse(os.getenv('DATABASE_URL', 'postgresql://studio_test@127.0.0.1:55432/python_studio'))
# Managed providers (Neon, Vercel Postgres) require TLS; carry sslmode through from the connection string.
db_query = dict(parse_qsl(url.query))
db_options = {'connect_timeout': 5}
if db_query.get('sslmode'):
    db_options['sslmode'] = db_query['sslmode']
DATABASES = {'default': {'ENGINE': 'django.db.backends.postgresql', 'NAME': unquote(url.path.lstrip('/')), 'USER': unquote(url.username or ''), 'PASSWORD': unquote(url.password or ''), 'HOST': url.hostname, 'PORT': url.port or 5432, 'OPTIONS': db_options}}
if os.getenv('USE_SQLITE', '').lower() == 'true':
    DATABASES = {'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': BASE_DIR / 'development.sqlite3'}}
AUTH_PASSWORD_VALIDATORS = [{'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'}, {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'}, {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'}, {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'}]
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_TZ = True
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
if not DEBUG:
    STORAGES = {'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'}, 'staticfiles': {'BACKEND': 'whitenoise.storage.CompressedStaticFilesStorage'}}
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
SESSION_COOKIE_SECURE = os.getenv('DJANGO_SECURE_COOKIES', 'false').lower() == 'true'
CSRF_COOKIE_SECURE = SESSION_COOKIE_SECURE
# Vercel terminates TLS at its proxy and forwards x-forwarded-proto; trust it so Django knows the request is secure.
if os.getenv('DJANGO_BEHIND_PROXY', 'false').lower() == 'true':
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
CSRF_TRUSTED_ORIGINS = [origin for origin in os.getenv('DJANGO_CSRF_TRUSTED_ORIGINS', 'http://localhost:5174,http://127.0.0.1:5174').split(',') if origin]
DATA_UPLOAD_MAX_MEMORY_SIZE = 100_000
REST_FRAMEWORK = {'DEFAULT_AUTHENTICATION_CLASSES': ['rest_framework.authentication.SessionAuthentication'], 'DEFAULT_PERMISSION_CLASSES': ['rest_framework.permissions.IsAuthenticated'], 'DEFAULT_THROTTLE_CLASSES': ['rest_framework.throttling.AnonRateThrottle', 'rest_framework.throttling.UserRateThrottle'], 'DEFAULT_THROTTLE_RATES': {'anon': '120/minute', 'user': '240/minute', 'auth': '12/minute', 'mentor': '10/minute'}}
OLLAMA_BASE_URL = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434').rstrip('/')
OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', '[EXISTING_INSTALLED_MODEL]')
