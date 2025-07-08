from django import template
from datetime import timedelta

register = template.Library()

@register.filter
def duration_display(value):
    if not isinstance(value, timedelta):
        return "0 minutes"

    total_seconds = int(value.total_seconds())
    h = total_seconds // 3600
    m = (total_seconds % 3600) // 60

    if h > 0:
        return f"{h}h {m}m"
    return f"{m}m"
