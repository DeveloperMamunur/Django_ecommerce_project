
from django.utils.timezone import now, timedelta
from accounts.models import UserActivity

def mark_inactive_users_offline():
    timeout = now() - timedelta(minutes=5)
    UserActivity.objects.filter(is_online=True, last_activity__lt=timeout).update(is_online=False)


mark_inactive_users_offline()