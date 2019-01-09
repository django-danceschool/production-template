"""
Default Django settings for the production Django Dance School project template.

This file is a starting place for your production deployment of the Dance School Project.
It references most default settings.  A large number of these settings are also automatically
specified through included environment variables, and many other settings are configured by
default in the included file danceschool.default_settings.  So, you may never need to edit this file
unless you wish to enable/disable optional functionality, or you wish to install additional
Django apps.  But, anything that is configured elsewhere through one of those methods can 
also be directly overridden below.

As always, be very careful never to commit any sensitive information such as database credentials
or your Django Secret Key to any location where it could be accessible to unauthorized individuals.
"""

import os
from os import environ
import dj_database_url
import dj_email_url
from logging.handlers import SysLogHandler


from huey import RedisHuey
from redis import ConnectionPool

# This line imports a large number of defaults, so that
# they do not need to be specified here directly.
# You may always override these defaults below.
from danceschool.default_settings import *


def boolify(s):
    ''' translate environment variables to booleans '''
    if isinstance(s,bool) or isinstance(s,int):
        return s
    s = s.strip().lower()
    return int(s) if s.isdigit() else s == 'true'


def get_secret(secret_name):
    ''' For Docker Swarms, the secret key and Postgres info are kept in secrets, not in the environment. '''
    try:
        with open('/run/secrets/{0}'.format(secret_name), 'r') as secret_file:
            return secret_file.read().rstrip('\n')
    except IOError:
        return None


# This line is required by Django CMS to determine default URLs
# for pages.
SITE_ID = 1

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.10/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = get_secret('django_secret_key') or environ.get('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = boolify(environ.get('DEBUG', False))

# SECURITY WARNING: ALLOWED_HOSTS must be updated for production
# to permit public access of the site.  Because *.herokuapp.com
# is currently allowed, this project is insecure by default.
# It is STRONGLY recommended that you update this to limit
# to your own domain before making your site public.
ALLOWED_HOSTS = ['127.0.0.1', 'localhost', 'testserver', environ.get('ALLOWED_HOST') or '']


# Application definition

INSTALLED_APPS = [
    # The CMS App goes first so that it will find plugins in other installed apps
    'cms',

    # The dynamic preferences app goes second so that it will find and register
    # project preferences in other installed apps
    'dynamic_preferences',

    # ## Typically, if you have a custom app for custom functionality,
    # ## it will be added here:
    # '< my_custom_app >',

    # The project provides some default theming options, including easy Bootstrap 4
    # plugins. As additional themes are included in the project, they should be added
    # here.  Uncomment a theme to enable the project to search for its template
    # files, CMS plugins, etc.  Also, be sure that the danceschool.themes app is
    # enabled below.
    'danceschool.themes.business_frontpage',

    # This is required for customizable themes to work, but it must be
    # listed *after* and customizable themes are listed so that templates
    # can be overridden as needed.
    'danceschool.themes',

    # ## This is the core app of the django-danceschool project that
    # ## is required for all installations:
    'danceschool.core',

    # ## These apps provide additional functionality and are optional,
    # ## but they are enabled by default:
    'danceschool.financial',
    'danceschool.private_events',
    'danceschool.discounts',
    'danceschool.vouchers',
    'danceschool.prerequisites',
    'danceschool.stats',
    'danceschool.news',
    'danceschool.faq',
    'danceschool.banlist',
    'danceschool.guestlist',

    # ## Uncomment to add private lesson scheduling functionality:
    # 'danceschool.private_lessons',

    # Note: Payment processor apps are automatically enabled/disabled below.
    # Except for the "Pay at door" app, which requires no external configuation
    # tokens or other environment variables to be present.
    # 'danceschool.payments.payatdoor',

    # These are required for the CMS
    'menus',
    'sekizai',
    'treebeard',

    # Django-admin-sortable permits us to drag and drop sort page content items
    'adminsortable2',

    # Django-allauth is used for better authentication options
    'allauth',
    'allauth.account',
    'allauth.socialaccount',

    # For rich text in Django CMS
    'ckeditor_filebrowser_filer',
    'djangocms_text_ckeditor',

    # For picking colors
    'colorful',

    # This helps to make forms pretty
    'crispy_forms',

    # For Bootstrap 4 plugins and theme functionality
    'djangocms_icon',
    'djangocms_link',
    'djangocms_picture',
    'djangocms_bootstrap4',
    'djangocms_bootstrap4.contrib.bootstrap4_alerts',
    'djangocms_bootstrap4.contrib.bootstrap4_badge',
    'djangocms_bootstrap4.contrib.bootstrap4_card',
    'djangocms_bootstrap4.contrib.bootstrap4_carousel',
    'djangocms_bootstrap4.contrib.bootstrap4_collapse',
    'djangocms_bootstrap4.contrib.bootstrap4_content',
    'djangocms_bootstrap4.contrib.bootstrap4_grid',
    'djangocms_bootstrap4.contrib.bootstrap4_jumbotron',
    'djangocms_bootstrap4.contrib.bootstrap4_link',
    'djangocms_bootstrap4.contrib.bootstrap4_listgroup',
    'djangocms_bootstrap4.contrib.bootstrap4_media',
    'djangocms_bootstrap4.contrib.bootstrap4_picture',
    'djangocms_bootstrap4.contrib.bootstrap4_tabs',
    'djangocms_bootstrap4.contrib.bootstrap4_utilities',

    # Autocomplete overrides some admin features so it goes here (above admin)
    'dal',
    'dal_select2',

    # This allows for custom date range filtering of financials, etc.
    'daterange_filter',

    # Makes Django CMS prettier
    'djangocms_admin_style',

    # Provides configurable feedback and response forms
    'djangocms_forms',

    # This allows for PDF export of views
    'easy_pdf',

    # Django-filer allows for file and image management
    'easy_thumbnails',
    'filer',

    # This permits simple task scheduling
    'huey.contrib.djhuey',

    # Django-polymorphic is used for Event multi-table inheritance
    'polymorphic',

    # Django-storages allows use of Amazon S3 or other solutions for
    # hosting user uploaded files
    'storages',

    # Disable Django's own staticfiles handling in favour of WhiteNoise, for
    # greater consistency between gunicorn and `./manage.py runserver`. See:
    # http://whitenoise.evans.io/en/stable/django.html#using-whitenoise-in-development
    'whitenoise.runserver_nostatic',

    # Finally, the Django contrib apps needed for this project and
    # its dependencies
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    'django.contrib.sitemaps',
    'django.contrib.admin',
]

MIDDLEWARE = [
    # This middleware is required by Django CMS for intelligent reloading on updates.
    'cms.middleware.utils.ApphookReloadMiddleware',
    # This middleware is used by WhiteNoise for static file handling
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    # These pieces of middleware are required by Django CMS
    'cms.middleware.user.CurrentUserMiddleware',
    'cms.middleware.page.CurrentPageMiddleware',
    'cms.middleware.toolbar.ToolbarMiddleware',
    'cms.middleware.language.LanguageCookieMiddleware',
]

ROOT_URLCONF = 'school.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'APP_DIRS': True,
        'OPTIONS': {
            # List of callables that know how to import templates from various sources.
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.template.context_processors.debug',
                'django.template.context_processors.i18n',
                'django.template.context_processors.media',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.static',
                'django.template.context_processors.csrf',
                'sekizai.context_processors.sekizai',
                'cms.context_processors.cms_settings',
                'danceschool.core.context_processors.site',
            ],
            'debug': False,
        },
    }
]

WSGI_APPLICATION = 'school.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.10/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}

# Change 'default' database configuration with $DATABASE_URL or the Docker secret.
DB_URL = get_secret('postgres_url') or environ.get('DATABASE_URL')
DATABASES['default'].update(dj_database_url.config(default=DB_URL,conn_max_age=500))

# Password validation
# https://docs.djangoproject.com/en/1.10/ref/settings/#auth-password-validators

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

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        }
    },
    'formatters': {
        'verbose': {
            'format': '[contactor] %(levelname)s %(asctime)s %(message)s'
        },
    },
    'handlers': {
        # Send messages to console based on environment logging level
        'console': {
            'level': environ.get('LOGGING_LEVEL','DEBUG'),
            'class': 'logging.StreamHandler',
        },
        # Send info messages to syslog
        'syslog':{
            'level':'INFO',
            'class': 'logging.handlers.SysLogHandler',
            'facility': SysLogHandler.LOG_LOCAL2,
            'address': '/dev/log',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        # This is the "catch all" logger
        '': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'boto': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        }
    }
}

# Internationalization
# https://docs.djangoproject.com/en/1.10/topics/i18n/

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en'

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
TIME_ZONE = environ.get('TIME_ZONE','America/New_York')

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Huey setup (use Redis by default)
pool = ConnectionPool.from_url(environ.get('REDIS_URL'))
HUEY = RedisHuey('danceschool', connection_pool=pool)

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.10/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(PROJECT_ROOT, 'staticfiles')

# Simplified static file serving.
# https://warehouse.python.org/project/whitenoise/
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Honor the 'X-Forwarded-Proto' header for request.is_secure()
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# AWS must be configured in the environment variables.  If it is
# not configured, then the project will default to local storage.
if (
    'AWS_STORAGE_BUCKET_NAME' in environ and
    'AWS_SECRET_ACCESS_KEY' in environ and
    'AWS_STORAGE_BUCKET_NAME' in environ
):
    DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
    AWS_ACCESS_KEY_ID = environ.get('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = environ.get('AWS_SECRET_ACCESS_KEY')
    AWS_STORAGE_BUCKET_NAME = environ.get('AWS_STORAGE_BUCKET_NAME')
else:
    MEDIA_ROOT = os.path.join(PROJECT_ROOT, 'media')
    MEDIA_URL = '/media/'

# Payment processor details are loaded here, if they have been added
# as environment variables

# Paypal
PAYPAL_MODE = environ.get('PAYPAL_MODE', 'sandbox')
PAYPAL_CLIENT_ID = environ.get('PAYPAL_CLIENT_ID')
PAYPAL_CLIENT_SECRET = environ.get('PAYPAL_CLIENT_SECRET')

if PAYPAL_MODE and PAYPAL_CLIENT_ID and PAYPAL_CLIENT_SECRET:
    INSTALLED_APPS.append('danceschool.payments.paypal')

# Square
SQUARE_LOCATION_ID = environ.get('SQUARE_LOCATION_ID')
SQUARE_APPLICATION_ID = environ.get('SQUARE_APPLICATION_ID')
SQUARE_ACCESS_TOKEN = environ.get('SQUARE_ACCESS_TOKEN')

if SQUARE_LOCATION_ID and SQUARE_ACCESS_TOKEN and SQUARE_APPLICATION_ID:
    INSTALLED_APPS.append('danceschool.payments.square')

# Stripe
STRIPE_PUBLIC_KEY = environ.get('STRIPE_PUBLIC_KEY')
STRIPE_PRIVATE_KEY = environ.get('STRIPE_PRIVATE_KEY')

if STRIPE_PUBLIC_KEY and STRIPE_PRIVATE_KEY:
    INSTALLED_APPS.append('danceschool.payments.stripe')

# Set Email using dj_email_url which parses $EMAIL_URL.
# Note: Sendgrid has been removed becuase of API issues; use
# SMTP integration for Sendgrid.
if 'EMAIL_URL' in environ:
    email_config = dj_email_url.config()
    EMAIL_FILE_PATH = email_config.get('EMAIL_FILE_PATH')
    EMAIL_HOST_USER = email_config.get('EMAIL_HOST_USER')
    EMAIL_HOST_PASSWORD = email_config.get('EMAIL_HOST_PASSWORD')
    EMAIL_HOST = email_config.get('EMAIL_HOST')
    EMAIL_PORT = email_config.get('EMAIL_PORT')
    EMAIL_BACKEND = email_config.get('EMAIL_BACKEND')
    EMAIL_USE_TLS = email_config.get('EMAIL_USE_TLS')
    EMAIL_USE_SSL = email_config.get('EMAIL_USE_SSL')

# Use Redis for caching
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": environ.get('REDIS_URL'),
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        }
    }
}

SESSION_ENGINE = "django.contrib.sessions.backends.cache"
SESSION_CACHE_ALIAS = "default"

#: Useful settings if you are running on Heroku
#: The unique identifier for the application. eg. "9daa2797-e49b-4624-932f-ec3f9688e3da"
HEROKU_APP_ID = environ.get('HEROKU_APP_ID', None)

#: The application name. eg. "example-app"
HEROKU_APP_NAME = environ.get('HEROKU_APP_NAME', None)

#: The dyno identifier. eg. "1vac4117-c29f-4312-521e-ba4d8638c1ac"
HEROKU_DYNO_ID = environ.get('HEROKU_DYNO_ID', None)

#: The identifier for the current release. eg. "v42"
HEROKU_SLUG_ID = environ.get('HEROKU_SLUG_ID', None)

#: The commit hash for the current release. eg. "2c3a0b24069af49b3de35b8e8c26765c1dba9ff0"
HEROKU_SLUG_COMMIT = environ.get('HEROKU_SLUG_COMMIT', None)

#: The time and date the release was created. eg. "2015/04/02 18:00:42"
HEROKU_RELEASE_CREATED_AT = environ.get('HEROKU_RELEASE_CREATED_AT', None)

#: The description of the current release. eg. "Deploy 2c3a0b2"
HEROKU_RELEASE_DESCRIPTION = environ.get('HEROKU_RELEASE_DESCRIPTION', None)
