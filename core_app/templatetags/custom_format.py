from django import template

register = template.Library()


@register.filter
def format_header(value):
    return value.split(".")[-1].replace("_", " ").title()

