from django import template

register = template.Library()

@register.filter
def multiply_and_format(value, arg):
    try:
        return "{:.2f}".format(value * float(arg))
    except (ValueError, TypeError):
        return value