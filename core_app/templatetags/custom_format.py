from django import template
from django.template.defaulttags import register

register = template.Library()


@register.filter
def display_zero(value):
    return "" if value == 0 else value


@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)


@register.filter
def format_title(value):
    """
    Input: 'revision_number'
    Output: 'Revision Number'
    """
    return " ".join([item.title() for item in value.split("_")])
