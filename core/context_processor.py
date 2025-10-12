from accounts.models import Profile
from django.contrib.auth.models import User
from accounts.models import UserPermission
from .models import MenuList
from .permissions import CheckUserPermission


def get_user_type(request):
    if request.user.is_authenticated:
        user = User.objects.get(username=request.user, is_active=True)
        return {
            "is_superuser": user.is_superuser,
            "is_staff": user.is_staff,
            "is_customer": not user.is_superuser and not user.is_staff
        }
    else:
        return {
            "is_superuser": False,
            "is_staff": False,
            "is_customer": False
        }


def menu_permissions(request):
    if not request.user.is_authenticated:
        return {}
    view_all_user = request.user.is_superuser or CheckUserPermission(request, 'can_view', 'accounts:all_user_list')
    view_user_activity = request.user.is_superuser or CheckUserPermission(request, 'can_view', 'accounts:user_activity_list')
    view_user_access_log = request.user.is_superuser or CheckUserPermission(request, 'can_view', 'accounts:user_access_log_list')
    view_user_details = request.user.is_superuser or CheckUserPermission(request, 'can_view', 'accounts:user_detail')
    update_user_status = request.user.is_superuser or CheckUserPermission(request, 'can_update', 'accounts:toggle_user_status')
    
    return {
        'can_view_all_user': view_all_user,
        'can_view_user_activity': view_user_activity,
        'can_view_user_access_log': view_user_access_log,
        'can_view_user_details': view_user_details,
        'can_update_user_status': update_user_status,
    }

