# Django settings for lavkushfurniture project.

from pathlib import Path
import os
from decouple import config
import cloudinary
# import dj_database_url

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Database settings (SQLite for development)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Quick-start development settings - unsuitable for production
SECRET_KEY = config('SECRET_KEY') # Use a secret key from your .env file

DEBUG = config('DEBUG', default=False, cast=bool)

ALLOWED_HOSTS = ['lavkushfurniture.onrender.com', 'localhost']

ALLOWED_HOSTS = config('ALLOWED_HOSTS', cast=lambda v: [s.strip() for s in v.split(',')])

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',  # required for allauth (if used)
    'account',
    'gallery',
    'team',
    'cloudinary',
    'cloudinary_storage',
]

MIDDLEWARE = [
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'lavkushfurniture.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        # 'DIRS': [BASE_DIR, "templates"],
        'DIRS': [BASE_DIR / "templates"],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'lavkushfurniture.wsgi.application'

# Password validation settings
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

# Internationalization settings
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images) settings
STATIC_URL = '/static/'

# STATICFILES_DIRS = [BASE_DIR / "static",]

STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]  # OR use BASE_DIR / 'static' if you're using Path()

STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Email configuration
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'jayeshkalkate432@gmail.com'  # Replace with your email
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD')  # Use app password securely

# Site ID (required by Django allauth if used)
SITE_ID = 1

# Media settings for file handling
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Login URL configuration
LOGIN_URL = 'login'  # This should match the name used in urls.py for login

# Cloudinary settings (using environment variables)
CLOUDINARY_STORAGE = {
    'CLOUD_NAME': config('CLOUDINARY_CLOUD_NAME'),
    'API_KEY': config('CLOUDINARY_API_KEY'),
    'API_SECRET': config('CLOUDINARY_API_SECRET'),
}

DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'

# Configure Cloudinary manually for template rendering
# cloudinary.config(
#     cloud_name=config('CLOUDINARY_CLOUD_NAME'),
#     api_key=config('CLOUDINARY_API_KEY'),
#     api_secret=config('CLOUDINARY_API_SECRET')
# )
