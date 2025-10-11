from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from core.models import TimeStampedModel, SoftDeleteModel, AuditModel
from core.models.menu import MenuList


# Create your models here.
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone = models.CharField(max_length=20)
    address = models.CharField(max_length=200)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    country = models.CharField(max_length=100)
    zipcode = models.CharField(max_length=10)
    profile_pic = models.ImageField(upload_to='profile_pics', blank=True)

    def __str__(self):
        return self.user.username

    class Meta:
        verbose_name = 'Profile'
        verbose_name_plural = 'Profiles'

class UserPermission(TimeStampedModel, SoftDeleteModel, AuditModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='permissions')
    menu = models.ForeignKey(MenuList, on_delete=models.CASCADE, related_name='user_permissions')
    can_view = models.BooleanField(default=False)
    can_create = models.BooleanField(default=False)
    can_update = models.BooleanField(default=False)
    can_delete = models.BooleanField(default=False)
    can_export = models.BooleanField(default=False)

    class Meta:
        db_table = 'user_permissions'
        unique_together = ('user', 'menu')

    def __str__(self):
        return str(self.menu)

class UserActivity(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='activity')
    
    # Session Info
    last_activity = models.DateTimeField(default=timezone.now)
    current_ip = models.GenericIPAddressField(null=True, blank=True)
    current_device = models.CharField(max_length=50, blank=True)
    current_browser = models.CharField(max_length=50, blank=True)

    # Auth Info
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)
    last_login_time = models.DateTimeField(null=True, blank=True)
    last_logout_time = models.DateTimeField(null=True, blank=True)
    
    is_online = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username} Activity"

    def update_activity(self, request):
        from user_agents import parse
        user_agent_str = request.META.get('HTTP_USER_AGENT', '')
        user_agent = parse(user_agent_str)

        self.last_activity = timezone.now()
        self.current_ip = self.get_client_ip(request)
        self.current_device = user_agent.device.family or "Unknown Device"
        self.current_browser = f"{user_agent.browser.family} {user_agent.browser.version_string}"
        self.current_os = f"{user_agent.os.family} {user_agent.os.version_string}"
        self.user_agent = user_agent_str  # (Add this field in your model if useful)
        self.is_online = True
        self.save()

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR')


class UserAccessLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    ip_address = models.GenericIPAddressField()
    device_type = models.CharField(max_length=50)
    browser = models.CharField(max_length=50)
    os = models.CharField(max_length=50)
    user_agent = models.TextField()
    login_time = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"AccessLog: {self.user} at {self.login_time}"