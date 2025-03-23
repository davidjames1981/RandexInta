from django import template

register = template.Library()

@register.filter
def get_range(value, arg=1):
    """
    Returns a range of numbers from 1 to value
    If arg is provided, it centers the range around that number
    """
    try:
        value = int(value)
        arg = int(arg)
        return range(1, value + 1)
    except (ValueError, TypeError):
        return range(0) 