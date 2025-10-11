from django.contrib import admin
from .models import Profile, UserActivity, UserAccessLog

# Register your models here.
admin.site.register(Profile)
admin.site.register(UserActivity)
admin.site.register(UserAccessLog)
