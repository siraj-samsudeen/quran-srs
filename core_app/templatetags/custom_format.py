from django import template
from django.template.defaulttags import register

register = template.Library()


@register.filter
def format_header(value):
    # Display  "8.scheduled_due_date" as "Scheduled Due Date"
    return value.split(".")[-1].replace("_", " ").title()


@register.filter
def display_zero(value):
    return "" if value == 0 else value


@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)
