# Django settings for derbysite project.
import os

CURRENT_PATH = os.path.abspath(os.path.dirname(__file__))

DEBUG = True

ADMINS = (
    ('John Schleigh', 'johnschleigh@gmail.com'),
    ('admin', ''),
    ('Robb Jones', 'robb.kc.jones@gmail.com'),
)

MANAGERS = ADMINS

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',  # Add 'postgresql_psycopg2', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': os.path.join(CURRENT_PATH, '../derby.db'),  # Or path to database file if using sqlite3.
        # The following settings are not used with sqlite3:
        'USER': '',  # robb
        'PASSWORD': '',  # alb....r
        'HOST': '',  # Empty for localhost through domain sockets or '127.0.0.1' for localhost through TCP.
        'PORT': '',  # Set to empty string for default.
    }
}

# Hosts/domain names that are valid for this site; required if DEBUG is False
# See https://docs.djangoproject.com/en/1.5/ref/settings/#allowed-hosts
ALLOWED_HOSTS = ['*']

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# In a Windows environment this must be set to your system time zone.
# TODO: Find a way to use system default
TIME_ZONE = 'America/Chicago'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

# 1 = Monday
FIRST_DAY_OF_WEEK = 1

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = False

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale.
USE_L10N = True

TIME_INPUT_FORMATS = ('%H:%M:%S.%f',)  # '14:30:59.000200'

# If you set this to False, Django will not use timezone-aware datetimes.
USE_TZ = False

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://example.com/media/", "http://media.example.com/"
# MEDIA_URL = 'http://agrippa:8000/admin/runner/media/'
MEDIA_ROOT = os.path.join(CURRENT_PATH, 'media')
MEDIA_URL = '/media/'

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/var/www/example.com/static/"
STATIC_ROOT = os.path.join(CURRENT_PATH, '../hosted-static/')
# print 'STATIC_ROOT={}'.format(STATIC_ROOT)

# URL prefix for static files.
# Example: "http://example.com/static/", "http://static.example.com/"
STATIC_URL = '/static/'

# Additional locations of static files
STATICFILES_DIRS = (
    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    os.path.join(CURRENT_PATH, '../static-files/'),
)

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
)

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'pegzkahb1e0q25wi8+c7tc)qg_vs$wz6_ql5owq=lt-!(04u4c'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            # insert your TEMPLATE_DIRS here
            ''.join((CURRENT_PATH, '../runner/templates')),
        ],
        'APP_DIRS': False,
        'OPTIONS': {
            'debug': True,
            'context_processors': [
                'django.contrib.auth.context_processors.auth',
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.template.context_processors.i18n',
                'django.template.context_processors.media',
                'django.template.context_processors.static',
                'django.template.context_processors.tz',
                'django.contrib.messages.context_processors.messages'
            ],
            'loaders': [
                'django.template.loaders.filesystem.Loader',
                'django.template.loaders.app_directories.Loader',
                'admin_tools.template_loaders.Loader',
            ],
        }
    }
]

MIDDLEWARE = (
    # MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    # Uncomment the next line for simple clickjacking protection:
    # 'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

ROOT_URLCONF = 'derbysite.urls'

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = 'derbysite.wsgi.application'

TEST_RUNNER = 'django.test.runner.DiscoverRunner'

INSTALLED_APPS = (
    'admin_tools',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'flat_responsive',
    'django.contrib.admin',
    'django.contrib.admindocs',
    'django.contrib.humanize',
    'runner'
)

SESSION_SERIALIZER = 'django.contrib.sessions.serializers.JSONSerializer'

LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s'
        },
        'medium': {
            'format': '%(asctime)s %(levelname)s %(message)s'
        },
        'simple': {
            'format': '%(levelname)s %(message)s'
        },
        'bare': {
            'format': '%(asctime)s %(message)s'
        },
    },
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        }
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'medium',
            'stream': 'ext://sys.stderr'
        },
        'debugfile': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': 'log/debug.log',
            'maxBytes': 1000000,
            'formatter': 'verbose'
        },
        'adminfile': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': 'log/admin.log',
            'maxBytes': 1000000,
            'formatter': 'verbose'
        },
        'track_raw_data_file': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': 'log/track_raw_data.log',
            'maxBytes': 1000000,
            'formatter': 'bare'
        },
        'sqlfile': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': 'log/sql.log',
            'maxBytes': 1000000,
            'formatter': 'verbose'
        },
        'tornadofile': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': 'log/tornado.log',
            'maxBytes': 1000000,
            'formatter': 'verbose'
        }, },
    'loggers': {
        'runner': {
            'handlers': ['console',
                         'debugfile'],
            'level': 'DEBUG',
            'propagate': False
        },
        'track_reader': {
            'handlers': ['console',
                         'track_raw_data_file'],
            'level': 'DEBUG',
            'propagate': False
        },
        'django.db': {
            'handlers': ['sqlfile'],
            'propagate': False,
            'level': 'DEBUG'
        },
        'tornado': {
            'handlers': [  # 'console',
                'tornadofile'],
            'level': 'DEBUG',
            'propagate': True
        },
        'admin': {
            'handlers': ['console',
                         'adminfile'],
            'level': 'DEBUG',
            'propagate': True
        }
    }
}

import django

django.setup()
