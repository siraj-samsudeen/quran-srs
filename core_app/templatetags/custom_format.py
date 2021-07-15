from django import template
from django.template.defaulttags import register

register = template.Library()


@register.filter
def display_zero(value):
    return "" if value == 0 else value


@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)
