from django.db.models.signals import post_save
from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import UserActivity, UserAccessLog
from django.utils.timezone import now
from user_agents import parse



@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    user_agent_str = request.META.get('HTTP_USER_AGENT', '')
    user_agent = parse(user_agent_str)

    ip = request.META.get('HTTP_X_FORWARDED_FOR', request.META.get('REMOTE_ADDR')).split(',')[0].strip()

    # Create log entry
    UserAccessLog.objects.create(
        user=user,
        ip_address=ip,
        device_type=user_agent.device.family,
        browser=user_agent.browser.family,
        os=user_agent.os.family,
        user_agent=user_agent_str,
    )

    # Update activity
    activity, _ = UserActivity.objects.get_or_create(user=user)
    activity.last_login_time = now()
    activity.last_login_ip = ip
    activity.is_online = True
    activity.save()

@receiver(user_logged_out)
def log_user_logout(sender, request, user, **kwargs):
    activity = getattr(user, 'activity', None)
    if activity:
        activity.is_online = False
        activity.last_logout_time = now()
        activity.save()