import os

DEBUG = True
ALLOWED_HOSTS = ["*"]

SECRET_KEY = "gsoc-prototype-not-for-production"

INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "django.contrib.sessions",
    "django.contrib.messages",
]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        # Use a file-based DB so the live_server thread and test thread
        # share the same data. :memory: creates a separate DB per connection.
        "NAME": "test_prototype.sqlite3",
    }
}

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    }
}

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates")],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    }
]

MIDDLEWARE = [
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
]

SESSION_ENGINE = "django.contrib.sessions.backends.db"

USE_TZ = True
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
ROOT_URLCONF = "esp.urls"
WSGI_APPLICATION = "esp.wsgi.application"
LOGIN_URL = "/myesp/login/"
LOGIN_REDIRECT_URL = "/esp/"

FORCE_SCRIPT_NAME = ""
