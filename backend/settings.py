# backend/settings.py

import os
from pathlib import Path
from dotenv import load_dotenv
import dj_database_url
import warnings
import logging
from typing import Any
import sentry_sdk
from sentry_sdk.integrations.celery import CeleryIntegration
from sentry_sdk.integrations.django import DjangoIntegration
from sentry_sdk.integrations.logging import LoggingIntegration
from celery.schedules import crontab

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

SECRET_KEY = os.getenv("SECRET_KEY", "django-insecure-...")
DEBUG = os.getenv("DEBUG", "False").lower() == "true"
ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1,.herokuapp.com").split(
    ","
)

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "")
TWILIO_FROM_NUMBER = os.getenv("TWILIO_FROM_NUMBER", "")

ELASTICSEARCH_URL = os.getenv("ELASTICSEARCH_URL", "http://localhost:9200")

# Global API throttle rates
ANON_THROTTLE_RATE = os.getenv("GLOBAL_ANON_THROTTLE_RATE", "100/day")
USER_THROTTLE_RATE = os.getenv("GLOBAL_USER_THROTTLE_RATE", "1000/day")

SENTRY_DSN = os.getenv("SENTRY_DSN")
if SENTRY_DSN:
    logging_integration = LoggingIntegration(
        level=getattr(logging, LOG_LEVEL, logging.INFO),
        event_level=logging.ERROR,
    )
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[DjangoIntegration(), CeleryIntegration(), logging_integration],
        traces_sample_rate=1.0,
        send_default_pii=True,
    )

INSTALLED_APPS = [
    # Django core
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sites",
    "channels",
    # Third-party
    "corsheaders",
    "rest_framework",
    "rest_framework.authtoken",
    "dj_rest_auth",
    "dj_rest_auth.registration",
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "allauth.socialaccount.providers.google",
    "allauth.socialaccount.providers.facebook",
    "allauth.socialaccount.providers.instagram",
    "django_mongoengine",
    "django_mongoengine.mongo_admin",
    "drf_yasg",
    "graphene_django",
    "waffle",
    # Local apps
    "users",
    "products",
    "orders",
    "cart",
    "payments",
    "discounts",
    "reviews",
    "authentication",
    "audit",
]

SITE_ID = 2

AUTH_USER_MODEL = "users.User"

AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
]

SOCIALACCOUNT_PROVIDERS = {
    "google": {
        "APP": {
            "client_id": os.getenv("GOOGLE_CLIENT_ID", ""),
            "secret": os.getenv("GOOGLE_CLIENT_SECRET", ""),
            "key": "",
        },
        "SCOPE": ["profile", "email"],
        "AUTH_PARAMS": {"access_type": "online"},
    },
    "facebook": {
        "APP": {
            "client_id": os.getenv("FACEBOOK_APP_ID", ""),
            "secret": os.getenv("FACEBOOK_APP_SECRET", ""),
            "key": "",
        }
    },
    "instagram": {
        "APP": {
            "client_id": os.getenv("INSTAGRAM_APP_ID", ""),
            "secret": os.getenv("INSTAGRAM_APP_SECRET", ""),
            "key": "",
        }
    },
}

ACCOUNT_USER_MODEL_USERNAME_FIELD = "username"
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_USERNAME_REQUIRED = True
ACCOUNT_AUTHENTICATION_METHOD = "username_email"
ACCOUNT_EMAIL_VERIFICATION = "optional"
ACCOUNT_SIGNUP_REDIRECT_URL = "/"
ACCOUNT_LOGOUT_REDIRECT_URL = "/"

SOCIALACCOUNT_AUTO_SIGNUP = True
SOCIALACCOUNT_QUERY_EMAIL = True

ACCOUNT_ADAPTER = "allauth.account.adapter.DefaultAccountAdapter"
SOCIALACCOUNT_ADAPTER = "authentication.adapters.CustomSocialAccountAdapter"

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": 8},
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "audit.middleware.AuditLogMiddleware",
    "waffle.middleware.WaffleMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "backend.middleware.SecurityHeadersMiddleware",
]

ROOT_URLCONF = "backend.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "backend.wsgi.application"
ASGI_APPLICATION = "backend.asgi.application"

CHANNEL_LAYERS = {"default": {"BACKEND": "channels.layers.InMemoryChannelLayer"}}

DATABASE_URL = os.getenv("DATABASE_URL")

# Force a lightweight SQLite database during CI or explicit test runs to avoid
# network calls to external Postgres instances. The CI environment typically
# sets `CI=true`, while developers can use `TESTING=1` when running tests
# locally.
if os.getenv("CI") or os.getenv("TESTING"):
    DATABASE_URL = "sqlite:///db.sqlite3"

if DATABASE_URL and DATABASE_URL.startswith("sqlite"):
    DATABASES = {"default": dj_database_url.parse(DATABASE_URL, conn_max_age=600)}
elif DATABASE_URL:
    DATABASES = {
        "default": dj_database_url.parse(
            DATABASE_URL, conn_max_age=600, ssl_require=True
        )
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

MONGODB_URI = os.getenv("MONGODB_URI", os.getenv("MONGO_URI"))
if os.getenv("CI") or os.getenv("TESTING"):
    # Use a local Mongo URI during automated tests to avoid network lookups
    MONGODB_URI = "mongodb://localhost"

MONGODB_DATABASES = {
    "default": {
        "name": "website",
        "host": MONGODB_URI,
        "connect": False,
    }
}

STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "dummy")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "dummy")
if STRIPE_SECRET_KEY == "dummy" or STRIPE_WEBHOOK_SECRET == "dummy":  # nosec B105
    warnings.warn(
        "Stripe keys are not set. Use valid keys in production.",
        RuntimeWarning,
    )

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")
STATICFILES_DIRS = [os.path.join(BASE_DIR, "static")]
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

MEDIA_URL = "/media/"
MEDIA_ROOT = os.path.join(BASE_DIR, "media")

# Allow configurable CORS origins via environment variable. If not provided,
# default to the deployed frontend and local development URLs.
_default_cors = [
    "https://twiinz-beard-frontend.netlify.app",
    FRONTEND_URL,
]
CORS_ALLOWED_ORIGINS = [
    origin.strip().rstrip("/")
    for origin in os.getenv("CORS_ALLOWED_ORIGINS", ",".join(_default_cors)).split(",")
    if origin.strip()
]
CORS_ALLOW_CREDENTIALS = True

CSRF_TRUSTED_ORIGINS = [
    "https://twiinz-beard-frontend.netlify.app",
    "https://twiinz-beard-backend-11dfd7158830.herokuapp.com",
]

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {
            "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "json",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": LOG_LEVEL,
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": LOG_LEVEL,
            "propagate": False,
        },
        "products.views": {
            "handlers": ["console"],
            "level": LOG_LEVEL,
            "propagate": False,
        },
        "mongoengine": {
            "handlers": ["console"],
            "level": LOG_LEVEL,
            "propagate": False,
        },
    },
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticatedOrReadOnly",
    ),
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": ANON_THROTTLE_RATE,
        "user": USER_THROTTLE_RATE,
        "login": "5/min",
        "review-create": "5/min",
    },
    "DEFAULT_VERSIONING_CLASS": "rest_framework.versioning.URLPathVersioning",
    "DEFAULT_VERSION": "v1",
    "ALLOWED_VERSIONS": ["v1"],
    "VERSION_PARAM": "version",
}

REST_USE_JWT = True
REST_AUTH_TOKEN_MODEL = None
REST_AUTH_SERIALIZERS = {
    "SOCIAL_LOGIN_SERIALIZER": "authentication.serializers.CustomSocialLoginSerializer",
}

GRAPHENE = {"SCHEMA": "backend.schema.schema"}

warnings.filterwarnings(
    "ignore", message="app_settings.USERNAME_REQUIRED is deprecated"
)
warnings.filterwarnings("ignore", message="app_settings.EMAIL_REQUIRED is deprecated")

# Celery configuration
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", CELERY_BROKER_URL)
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"

CELERY_BEAT_SCHEDULE = {
    "purge-inactive-carts": {
        "task": "cart.tasks.purge_inactive_carts",
        "schedule": crontab(hour=0, minute=0),
    },
    "cleanup-expired-sessions": {
        "task": "users.tasks.cleanup_expired_sessions",
        "schedule": crontab(hour=0, minute=0),
    },
}

CART_INACTIVITY_DAYS = int(os.getenv("CART_INACTIVITY_DAYS", "30"))

# Cache configuration
if os.getenv("CI") or os.getenv("TESTING"):
    CACHES: dict[str, dict[str, Any]] = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        }
    }
else:
    cache_urls = os.getenv("CACHE_URLS")
    if cache_urls:
        CACHES = {
            "default": {
                "BACKEND": "django_redis.cache.RedisCache",
                "LOCATION": [url.strip() for url in cache_urls.split(",")],
                "OPTIONS": {
                    "CLIENT_CLASS": "django_redis.client.DefaultClient",
                    "REDIS_CLIENT_CLASS": "redis.cluster.RedisCluster",
                    "CONNECTION_POOL_CLASS": "redis.cluster.ClusterConnectionPool",
                },
            }
        }
    else:
        CACHE_URL = os.getenv("CACHE_URL", "redis://localhost:6379/1")
        CACHES = {
            "default": {
                "BACKEND": "django_redis.cache.RedisCache",
                "LOCATION": CACHE_URL,
                "OPTIONS": {
                    "CLIENT_CLASS": "django_redis.client.DefaultClient",
                },
            }
        }

# Security settings
SECURE_SSL_REDIRECT = os.getenv("SECURE_SSL_REDIRECT", "True") == "True"
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"
