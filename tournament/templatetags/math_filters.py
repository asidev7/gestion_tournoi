"""
Custom math filters for Django templates
"""
from django import template

register = template.Library()


@register.filter
def div(value, arg):
    """Divide value by arg"""
    try:
        return int(value) / int(arg)
    except (ValueError, ZeroDivisionError):
        return 0


@register.filter
def mul(value, arg):
    """Multiply value by arg"""
    try:
        return int(value) * int(arg)
    except ValueError:
        return 0


@register.filter
def sub(value, arg):
    """Subtract arg from value"""
    try:
        return int(value) - int(arg)
    except ValueError:
        return 0


@register.filter
def add(value, arg):
    """Add arg to value"""
    try:
        return int(value) + int(arg)
    except ValueError:
        return 0
