import re
from os import environ
from os.path import abspath, dirname, join
from typing import Any, Callable, Tuple

# For reference see https://docs.netbox.dev/en/stable/configuration/
# Based on https://github.com/netbox-community/netbox/blob/develop/netbox/netbox/configuration_example.py

###
# NetBox-Docker Helper functions
###


# Read secret from file
def _read_secret(secret_name: str, default: str | None = None) -> str | None:
    try:
        f = open('/run/secrets/' + secret_name, 'r', encoding='utf-8')
    except EnvironmentError:
        return default
    else:
        with f:
            return f.readline().strip()


# If the `map_fn` isn't defined, then the value that is read from the environment (or the default value if not found) is returned.
# If the `map_fn` is defined, then `map_fn` is invoked and the value (that was read from the environment or the default value if not found)
# is passed to it as a parameter. The value returned from `map_fn` is then the return value of this function.
# The `map_fn` is not invoked, if the value (that was read from the environment or the default value if not found) is None.
def _environ_get_and_map(variable_name, default=None, map_fn=None):
    env_value = environ.get(variable_name, default)

    if env_value == None:
        return env_value

    if not map_fn:
        return env_value

    return map_fn(env_value)


_AS_BOOL = lambda value: value.lower() == 'true'
_AS_INT = lambda value: int(value)
_AS_LIST = lambda value: list(filter(None, value.split(' ')))

#########################
#                       #
#   Required settings   #
#                       #
#########################

# This is a list of valid fully-qualified domain names (FQDNs) for the NetBox server. NetBox will not permit write
# access to the server via any other hostnames. The first FQDN in the list will be treated as the preferred name.
#
# Example: ALLOWED_HOSTS = ['netbox.example.com', 'netbox.internal.local']
ALLOWED_HOSTS = environ.get('ALLOWED_HOSTS', '*').split(' ')
# ensure that '*' or 'localhost' is always in ALLOWED_HOSTS (needed for health checks)
if '*' not in ALLOWED_HOSTS and 'localhost' not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append('localhost')

# PostgreSQL database configuration. See the Django documentation for a complete list of available parameters:
#   https://docs.djangoproject.com/en/stable/ref/settings/#databases
DATABASES = {
    'default': {
        'NAME': environ.get('DB_NAME', 'netbox'),  # Database name
        'USER': environ.get('DB_USER', ''),  # PostgreSQL username
        'PASSWORD': _read_secret('db_password', environ.get('DB_PASSWORD', '')),
        # PostgreSQL password
        'HOST': environ.get('DB_HOST', 'localhost'),  # Database server
        'PORT': environ.get('DB_PORT', ''),  # Database port (leave blank for default)
        'OPTIONS': {'sslmode': environ.get('DB_SSLMODE', 'prefer')},
        # Database connection SSLMODE
        'CONN_MAX_AGE': _environ_get_and_map('DB_CONN_MAX_AGE', '300', _AS_INT),
        # Max database connection age
        'DISABLE_SERVER_SIDE_CURSORS': _environ_get_and_map('DB_DISABLE_SERVER_SIDE_CURSORS', 'False', _AS_BOOL),
        # Disable the use of server-side cursors transaction pooling
    }
}

# Redis database settings. Redis is used for caching and for queuing background tasks such as webhook events. A separate
# configuration exists for each. Full connection details are required in both sections, and it is strongly recommended
# to use two separate database IDs.
REDIS = {
    'tasks': {
        'HOST': environ.get('REDIS_HOST', 'localhost'),
        'PORT': _environ_get_and_map('REDIS_PORT', 6379, _AS_INT),
        'SENTINELS': [tuple(uri.split(':')) for uri in _environ_get_and_map('REDIS_SENTINELS', '', _AS_LIST) if uri != ''],  # type: ignore
        'SENTINEL_SERVICE': environ.get('REDIS_SENTINEL_SERVICE', 'default'),
        'SENTINEL_TIMEOUT': _environ_get_and_map('REDIS_SENTINEL_TIMEOUT', 10, _AS_INT),
        'USERNAME': environ.get('REDIS_USERNAME', ''),
        'PASSWORD': _read_secret('redis_password', environ.get('REDIS_PASSWORD', '')),
        'DATABASE': _environ_get_and_map('REDIS_DATABASE', 0, _AS_INT),
        'SSL': _environ_get_and_map('REDIS_SSL', 'False', _AS_BOOL),
        'INSECURE_SKIP_TLS_VERIFY': _environ_get_and_map('REDIS_INSECURE_SKIP_TLS_VERIFY', 'False', _AS_BOOL),
    },
    'caching': {
        'HOST': environ.get('REDIS_CACHE_HOST', environ.get('REDIS_HOST', 'localhost')),
        'PORT': _environ_get_and_map('REDIS_CACHE_PORT', environ.get('REDIS_PORT', '6379'), _AS_INT),
        'SENTINELS': [tuple(uri.split(':')) for uri in _environ_get_and_map('REDIS_CACHE_SENTINELS', '', _AS_LIST) if uri != ''],  # type: ignore
        'SENTINEL_SERVICE': environ.get(
            'REDIS_CACHE_SENTINEL_SERVICE', environ.get('REDIS_SENTINEL_SERVICE', 'default')
        ),
        'USERNAME': environ.get('REDIS_CACHE_USERNAME', environ.get('REDIS_USERNAME', '')),
        'PASSWORD': _read_secret(
            'redis_cache_password', environ.get('REDIS_CACHE_PASSWORD', environ.get('REDIS_PASSWORD', ''))
        ),
        'DATABASE': _environ_get_and_map('REDIS_CACHE_DATABASE', '1', _AS_INT),
        'SSL': _environ_get_and_map('REDIS_CACHE_SSL', environ.get('REDIS_SSL', 'False'), _AS_BOOL),
        'INSECURE_SKIP_TLS_VERIFY': _environ_get_and_map(
            'REDIS_CACHE_INSECURE_SKIP_TLS_VERIFY', environ.get('REDIS_INSECURE_SKIP_TLS_VERIFY', 'False'), _AS_BOOL
        ),
    },
}

# This key is used for secure generation of random numbers and strings. It must never be exposed outside of this file.
# For optimal security, SECRET_KEY should be at least 50 characters in length and contain a mix of letters, numbers, and
# symbols. NetBox will not run without this defined. For more information, see
# https://docs.djangoproject.com/en/stable/ref/settings/#std:setting-SECRET_KEY
SECRET_KEY = environ.get('SECRET_KEY', "dummydummydummydummydummydummydummydummydummydummy")

#########################
#                       #
#   Optional settings   #
#                       #
#########################

# Specify one or more name and email address tuples representing NetBox administrators. These people will be notified of
# application errors (assuming correct email settings are provided).
ADMINS = [
    # ('John Doe', 'jdoe@example.com'),
]

# Permit the retrieval of API tokens after their creation.
ALLOW_TOKEN_RETRIEVAL = False

# Enable any desired validators for local account passwords below. For a list of included validators, please see the
# Django documentation at https://docs.djangoproject.com/en/stable/topics/auth/passwords/#password-validation.
AUTH_PASSWORD_VALIDATORS = [
    # {
    #     'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    #     'OPTIONS': {
    #         'min_length': 10,
    #     }
    # },
]

# Base URL path if accessing NetBox within a directory. For example, if installed at https://example.com/netbox/, set:
# BASE_PATH = 'netbox/'
BASE_PATH = ''

# API Cross-Origin Resource Sharing (CORS) settings. If CORS_ORIGIN_ALLOW_ALL is set to True, all origins will be
# allowed. Otherwise, define a list of allowed origins using either CORS_ORIGIN_WHITELIST or
# CORS_ORIGIN_REGEX_WHITELIST. For more information, see https://github.com/ottoyiu/django-cors-headers
CORS_ORIGIN_ALLOW_ALL = False
CORS_ORIGIN_WHITELIST = [
    # 'https://hostname.example.com',
]
CORS_ORIGIN_REGEX_WHITELIST = [
    # r'^(https?://)?(\w+\.)?example\.com$',
]

# The name to use for the CSRF token cookie.
CSRF_COOKIE_NAME = 'csrftoken'

# Set to True to enable server debugging. WARNING: Debugging introduces a substantial performance penalty and may reveal
# sensitive information about your installation. Only enable debugging while performing testing. Never enable debugging
# on a production system.
DEBUG = False

# Set the default preferred language/locale
DEFAULT_LANGUAGE = 'en-us'

# Email settings
EMAIL = {
    'SERVER': 'localhost',
    'PORT': 25,
    'USERNAME': '',
    'PASSWORD': '',
    'USE_SSL': False,
    'USE_TLS': False,
    'TIMEOUT': 10,  # seconds
    'FROM_EMAIL': '',
}

# Exempt certain models from the enforcement of view permissions. Models listed here will be viewable by all users and
# by anonymous users. List models in the form `<app>.<model>`. Add '*' to this list to exempt all models.
EXEMPT_VIEW_PERMISSIONS = [
    # 'dcim.site',
    # 'dcim.region',
    # 'ipam.prefix',
]

# HTTP proxies NetBox should use when sending outbound HTTP requests (e.g. for webhooks).
# HTTP_PROXIES = {
#     'http': 'http://10.10.1.10:3128',
#     'https': 'http://10.10.1.10:1080',
# }

# IP addresses recognized as internal to the system. The debugging toolbar will be available only to clients accessing
# NetBox from an internal IP.
INTERNAL_IPS = ('127.0.0.1', '::1')

# Enable custom logging. Please see the Django documentation for detailed guidance on configuring custom logs:
#   https://docs.djangoproject.com/en/stable/topics/logging/
LOGGING = {}

# Automatically reset the lifetime of a valid session upon each authenticated request. Enables users to remain
# authenticated to NetBox indefinitely.
LOGIN_PERSISTENCE = False

# Setting this to False will permit unauthenticated users to access most areas of NetBox (but not make any changes).
LOGIN_REQUIRED = True

# The length of time (in seconds) for which a user will remain logged into the web UI before being prompted to
# re-authenticate. (Default: 1209600 [14 days])
LOGIN_TIMEOUT = None

# Hide the login form. Useful when only allowing SSO authentication.
LOGIN_FORM_HIDDEN = False

# The view name or URL to which users are redirected after logging out.
LOGOUT_REDIRECT_URL = 'home'

# The file path where uploaded media such as image attachments are stored. A trailing slash is not needed. Note that
# the default value of this setting is derived from the installed location.
# MEDIA_ROOT = '/opt/netbox/netbox/media'

# Expose Prometheus monitoring metrics at the HTTP endpoint '/metrics'
METRICS_ENABLED = False

PLUGINS = [
    "netbox_inventory",
    "netbox_diode_plugin",
    "netbox_custom_objects",
    "netbox_branching",  # MUST BE THE LAST PLUGIN
]

PLUGINS_CONFIG = {
    "netbox_branching": {
        "exempt_models": [
            "netbox_custom_objects.customobjecttype",
            "netbox_custom_objects.customobjecttypefield",
        ],
    },
    "netbox_inventory": {
        "sync_hardware_serial_asset_tag": True,
    },
    "netbox_diode_plugin": {
        "diode_target_override": "grpc://localhost:8080/diode",
        "diode_username": "diode",
        "netbox_to_diode_client_secret": "2WkRG7RZOxN5taPbAlMkKoZjx5rHed51F7+bNyqf03U=",
    },
}

# Remote authentication support
REMOTE_AUTH_ENABLED = False
REMOTE_AUTH_BACKEND = 'netbox.authentication.RemoteUserBackend'
REMOTE_AUTH_HEADER = 'HTTP_REMOTE_USER'
REMOTE_AUTH_USER_FIRST_NAME = 'HTTP_REMOTE_USER_FIRST_NAME'
REMOTE_AUTH_USER_LAST_NAME = 'HTTP_REMOTE_USER_LAST_NAME'
REMOTE_AUTH_USER_EMAIL = 'HTTP_REMOTE_USER_EMAIL'
REMOTE_AUTH_AUTO_CREATE_USER = True
REMOTE_AUTH_DEFAULT_GROUPS = []
REMOTE_AUTH_DEFAULT_PERMISSIONS = {}

# This repository is used to check whether there is a new release of NetBox available. Set to None to disable the
# version check or use the URL below to check for release in the official NetBox repository.
RELEASE_CHECK_URL = None
# RELEASE_CHECK_URL = 'https://api.github.com/repos/netbox-community/netbox/releases'

# The file path where custom reports will be stored. A trailing slash is not needed. Note that the default value of
# this setting is derived from the installed location.
# REPORTS_ROOT = '/opt/netbox/netbox/reports'

# Maximum execution time for background tasks, in seconds.
RQ_DEFAULT_TIMEOUT = 300

# The file path where custom scripts will be stored. A trailing slash is not needed. Note that the default value of
# this setting is derived from the installed location.
# SCRIPTS_ROOT = '/opt/netbox/netbox/scripts'

# The name to use for the session cookie.
SESSION_COOKIE_NAME = 'sessionid'

# By default, NetBox will store session data in the database. Alternatively, a file path can be specified here to use
# local file storage instead. (This can be useful for enabling authentication on a standby instance with read-only
# database access.) Note that the user as which NetBox runs must have read and write permissions to this path.
SESSION_FILE_PATH = None

# By default the memory and disk sizes are displayed using base 10 (e.g. 1000 MB = 1 GB).
# If you would like to use base 2 (e.g. 1024 MB = 1 GB) set this to 1024.
# DISK_BASE_UNIT = 1024
# RAM_BASE_UNIT = 1024

# Within the STORAGES dictionary, "default" is used for image uploads, "staticfiles" is for static files and "scripts"
# is used for custom scripts. See django-storages and django-storage-swift libraries for more details. By default the
# following configuration is used:
# STORAGES = {
#     "default": {
#         "BACKEND": "django.core.files.storage.FileSystemStorage",
#     },
#     "staticfiles": {
#         "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
#     },
#     "scripts": {
#         "BACKEND": "extras.storage.ScriptFileSystemStorage",
#     },
# }

# Time zone (default: UTC)
TIME_ZONE = 'UTC'

DEBUG = True
DEVELOPER = True

#############################
#                           #
#  Branching Configuration  #
#                           #
#############################

from netbox_branching.utilities import DynamicSchemaDict

# This should be defined upstream by `/etc/netbox/config/netbox.yaml`
# and loaded in
DATABASES = DynamicSchemaDict(DATABASES)

DATABASE_ROUTERS = [
    'netbox_branching.database.BranchAwareRouter',
]
