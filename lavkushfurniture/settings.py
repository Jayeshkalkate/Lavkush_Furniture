import os
from pathlib import Path
from decouple import config
import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = config('SECRET_KEY', default='dev-only-change-me')
DEBUG = config('DEBUG', default=False, cast=bool)
if not DEBUG and len(SECRET_KEY) < 32:
    raise RuntimeError('SECRET_KEY must be a strong random value (32+ characters) when DEBUG=False.')

SITE_URL = config('SITE_URL', default='http://127.0.0.1:8000').rstrip('/')
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1', cast=lambda v: [s.strip() for s in v.split(',') if s.strip()])
# Render injects the service's public hostname; trust it so health checks and the site work
# even before ALLOWED_HOSTS / CSRF_TRUSTED_ORIGINS are set in the dashboard.
_render_host = config('RENDER_EXTERNAL_HOSTNAME', default='')
if _render_host and _render_host not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append(_render_host)
if not DEBUG and not ALLOWED_HOSTS:
    raise RuntimeError('ALLOWED_HOSTS must be configured when DEBUG=False.')
CSRF_TRUSTED_ORIGINS = config('CSRF_TRUSTED_ORIGINS', default='', cast=lambda v: [s.strip() for s in v.split(',') if s.strip()])
if _render_host and f'https://{_render_host}' not in CSRF_TRUSTED_ORIGINS:
    CSRF_TRUSTED_ORIGINS.append(f'https://{_render_host}')

# Database: SQLite for local development; PostgreSQL when DATABASE_URL is provided.
database_url = config('DATABASE_URL', default='')
if database_url:
    DATABASES = {'default': dj_database_url.parse(database_url, conn_max_age=600, ssl_require=database_url.startswith('postgres'))}
else:
    DATABASES = {'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': BASE_DIR / 'db.sqlite3'}}

INSTALLED_APPS = [
    'django.contrib.admin', 'django.contrib.auth', 'django.contrib.contenttypes',
    'django.contrib.sessions', 'django.contrib.messages', 'django.contrib.staticfiles',
    'django.contrib.sites', 'django.contrib.sitemaps',
    'cloudinary', 'cloudinary_storage',
    'account', 'gallery', 'team', 'cart', 'order', 'wishlist', 'dashboard',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'lavkushfurniture.urls'
WSGI_APPLICATION = 'lavkushfurniture.wsgi.application'

TEMPLATES = [{
    'BACKEND': 'django.template.backends.django.DjangoTemplates',
    'DIRS': [BASE_DIR / 'templates'],
    'APP_DIRS': True,
    'OPTIONS': {'context_processors': [
        'django.template.context_processors.debug',
        'django.template.context_processors.request',
        'django.contrib.auth.context_processors.auth',
        'django.contrib.messages.context_processors.messages',
        'lavkushfurniture.context_processors.site_context',
    ]},
}]

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Kolkata'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Use Cloudinary only when its three credentials exist; otherwise store uploads locally.
cloudinary_name = config('CLOUDINARY_CLOUD_NAME', default='')
cloudinary_key = config('CLOUDINARY_API_KEY', default='')
cloudinary_secret = config('CLOUDINARY_API_SECRET', default='')
USE_CLOUDINARY = all([cloudinary_name, cloudinary_key, cloudinary_secret])

WHITENOISE_MANIFEST_STRICT = False

STORAGES = {
    'staticfiles': {'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage'},
    'default': {'BACKEND': 'cloudinary_storage.storage.MediaCloudinaryStorage' if USE_CLOUDINARY else 'django.core.files.storage.FileSystemStorage'},
}

if USE_CLOUDINARY:
    import cloudinary
    cloudinary.config(cloud_name=cloudinary_name, api_key=cloudinary_key, api_secret=cloudinary_secret)
    CLOUDINARY_STORAGE = {'CLOUD_NAME': cloudinary_name, 'API_KEY': cloudinary_key, 'API_SECRET': cloudinary_secret}

RAZORPAY_KEY_ID = config('RAZORPAY_KEY_ID', default='')
RAZORPAY_KEY_SECRET = config('RAZORPAY_KEY_SECRET', default='')
RAZORPAY_WEBHOOK_SECRET = config('RAZORPAY_WEBHOOK_SECRET', default='')

EMAIL_BACKEND = config('EMAIL_BACKEND', default='django.core.mail.backends.console.EmailBackend')
EMAIL_HOST = config('EMAIL_HOST', default='smtp.gmail.com')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='lavkushfurniture@gmail.com')

SITE_ID = 1
LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'homepage'
LOGOUT_REDIRECT_URL = 'login'
ADMIN_URL = config('ADMIN_URL', default='admin')
GST_RATE = config('GST_RATE', default=0, cast=float)
SHIPPING_FLAT_RATE = config('SHIPPING_FLAT_RATE', default=0, cast=float)
BULK_IMAGE_ALLOWED_HOSTS = config('BULK_IMAGE_ALLOWED_HOSTS', default='', cast=lambda v: [s.strip().lower() for s in v.split(',') if s.strip()])

# Production hardening. Keep DEBUG=true and local cookies for development.
SECURE_SSL_REDIRECT = config('SECURE_SSL_REDIRECT', default=not DEBUG, cast=bool)
SECURE_REDIRECT_EXEMPT = [r'^healthz/$']  # platform health checks arrive over plain HTTP
SESSION_COOKIE_SECURE = config('SESSION_COOKIE_SECURE', default=not DEBUG, cast=bool)
CSRF_COOKIE_SECURE = config('CSRF_COOKIE_SECURE', default=not DEBUG, cast=bool)
SECURE_HSTS_SECONDS = config('SECURE_HSTS_SECONDS', default=31536000 if not DEBUG else 0, cast=int)
SECURE_HSTS_INCLUDE_SUBDOMAINS = not DEBUG
SECURE_HSTS_PRELOAD = not DEBUG
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
X_FRAME_OPTIONS = 'DENY'

from django.contrib.messages import constants as message_constants
MESSAGE_TAGS = {message_constants.ERROR: 'danger'}

SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_AGE = 60 * 60 * 24 * 14
SESSION_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_SAMESITE = 'Lax'
DATA_UPLOAD_MAX_MEMORY_SIZE = 12 * 1024 * 1024
FILE_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024

CACHES = {'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache', 'LOCATION': 'lavkush-default'}}

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {'console': {'class': 'logging.StreamHandler'}},
    'loggers': {
        'django': {'handlers': ['console'], 'level': 'INFO'},
        'lavkushfurniture': {'handlers': ['console'], 'level': 'INFO', 'propagate': False},
        'account': {'handlers': ['console'], 'level': 'INFO', 'propagate': False},
        'gallery': {'handlers': ['console'], 'level': 'INFO', 'propagate': False},
        'order': {'handlers': ['console'], 'level': 'INFO', 'propagate': False},
        'cart': {'handlers': ['console'], 'level': 'INFO', 'propagate': False},
    },
}
