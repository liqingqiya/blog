#-*- coding:utf-8 -*-

DEBUG = True
TEMPLATE_DEBUG = DEBUG

import os
BASE_DIR = os.path.dirname(__file__)

ADMINS = (
)

MANAGERS = ADMINS

if 'SERVER_SOFTWARE' in os.environ:
    from sae.const import (
        MYSQL_HOST, MYSQL_PORT, MYSQL_USER, MYSQL_PASS, MYSQL_DB
    )
else:
    MYSQL_HOST = 'localhost'
    MYSQL_PORT = '3306'
    MYSQL_USER = 'root'
    MYSQL_PASS = ''
    MYSQL_DB   = 'blog_sae'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'OPTIONS'  : { 'init_command' : 'SET storage_engine=MYISAM', },
        'NAME': MYSQL_DB,                      # Or path to database file if using sqlite3.
        'USER': MYSQL_USER,                      # Not used with sqlite3.
        'PASSWORD': MYSQL_PASS,                  # Not used with sqlite3.
        'HOST': MYSQL_HOST,                      # Set to empty string for localhost. Not used with sqlite3.
        'PORT': MYSQL_PORT,                      # Set to empty string for default. Not used with sqlite3.
    }
}
# Hosts/domain names that are valid for this site; required if DEBUG is False
# See https://docs.djangoproject.com/en/1.5/ref/settings/#allowed-hosts
ALLOWED_HOSTS = []

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# In a Windows environment this must be set to your system time zone.
TIME_ZONE = 'America/Chicago'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale.
USE_L10N = True

# If you set this to False, Django will not use timezone-aware datetimes.
USE_TZ = True


# Additional locations of static files
STATICFILES_DIRS = (
    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
)

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
#    'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

# Make this unique, and don't share it with anybody.
SECRET_KEY = '8$+t5unsgu4eseyv77%)^#o1bh6+qq62+=!n-efut6whrjym78'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
#     'django.template.loaders.eggs.Loader',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    # Uncomment the next line for simple clickjacking protection:
    # 'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

ROOT_URLCONF = 'blog_sae.urls'

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = 'blog_sae.wsgi.application'

TEMPLATE_DIRS = (
    os.path.join(BASE_DIR, 'template'),
)


INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Uncomment the next line to enable the admin:
    'django.contrib.admin',
    # Uncomment the next line to enable admin documentation:
    # 'django.contrib.admindocs',

    "django.contrib.markup",
    "django_summernote",
    "crispy_forms",

    "blog_sae.blog",
    "blog_sae.show",
)

# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error when DEBUG=False.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        }
    },
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        }
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
    }
}


SESSION_COOKIE_AGE = 3600

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.6/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static')

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

#静态文件路径
CSS_URL = "/css/"
JS_URL = "/js/"
IMG_URL = "/img/"
FONTS_URL = "/fonts/"

CSS_ROOT = os.path.join(STATIC_ROOT, "css")
JS_ROOT = os.path.join(STATIC_ROOT, "js")
IMG_ROOT = os.path.join(STATIC_ROOT, "img")
FONTS_ROOT = os.path.join(STATIC_ROOT, "fonts")

DEFAULT_CHARSET='utf-8'

SUMMERNOTE_CONFIG = {
    #editor size
    'width': '80%',
    'height': '480',
    'lang': 'zh-CN',
    'toolbar': [
        ['style', ['style']],
        ['font', ['bold', 'italic', 'underline', 'superscript', 'subscript',
                  'strikethrough', 'clear']],
        ['fontname', ['fontname']],
        ['fontsize', ['fontsize']],
        ['color', ['color']],
        ['para', ['ul', 'ol', 'paragraph']],
        ['height', ['height']],
        ['table', ['table']],
        ['insert', ['link', 'picture', 'video', 'hr']],
        ['view', ['codeview']],
    ],
}

