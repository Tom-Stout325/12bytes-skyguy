from django import template

register = template.Library()

@register.filter
def lookup(dictionary, key):
    return dictionary.get(key, 0) 

@register.filter
def mul(value, arg):
    """Multiply the value by the arg."""
    try:
        return round(float(value) * float(arg), 2)
    except (ValueError, TypeError):
        return ''
