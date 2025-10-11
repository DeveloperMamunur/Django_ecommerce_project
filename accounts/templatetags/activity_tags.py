from django import template
from django.utils.timezone import now
from datetime import timedelta

register = template.Library()

@register.filter
def is_recent(activity_time, minutes=5):
    if not activity_time:
        return False
    return activity_time > now() - timedelta(minutes=minutes)
