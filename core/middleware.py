from accounts.models import UserActivity
from django.utils.timezone import now

class UserActivityMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        if request.user.is_authenticated:
            # Update only every X seconds instead of on every request
            activity, created = UserActivity.objects.get_or_create(user=request.user)
            if (now() - activity.last_activity).seconds > 30:  # update only every 30s
                activity.update_activity(request)

        return response