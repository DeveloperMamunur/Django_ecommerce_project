from django.contrib import admin
from .models import Profile, UserActivity, UserAccessLog,UserPermission

# Register your models here.
admin.site.register(Profile)
admin.site.register(UserActivity)
admin.site.register(UserAccessLog)
admin.site.register(UserPermission)
