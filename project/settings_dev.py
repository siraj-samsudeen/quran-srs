from project.settings import *

AUTH_PASSWORD_VALIDATORS = []

DEBUG = True

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "smd1equijn^3ex(6uu)tb1aslfeksymd7&e^wvih!eao0u*x2o"

# IP address might change on server restart. Hence, better to have a wildcard - 192.168.1.* TODO
ALLOWED_HOSTS = ["127.0.0.1", "0.0.0.0", "192.168.1.10"]
