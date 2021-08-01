from project.settings import *

AUTH_PASSWORD_VALIDATORS = []

DEBUG = True

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "smd1equijn^3ex(6uu)tb1aslfeksymd7&e^wvih!eao0u*x2o"

# IP address might change on server restart. Hence, better to have a wildcard - 192.168.1.* TODO
ALLOWED_HOSTS = ["127.0.0.1", "0.0.0.0", "192.168.1.10"]

# Changes to make live reload of static files - templates and js

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "livereload",
    "django.contrib.staticfiles",
    "core_app",
    "django_extensions",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "livereload.middleware.LiveReloadScript",
]
