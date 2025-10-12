from accounts.models import UserPermission
from django.contrib.auth.models import User

def CheckUserPermission(request, accessType, view_name):
    try:
        user_permissions = {
            'can_view': 'can_view',
            'can_create': 'can_create',
            'can_update': 'can_update',
            'can_delete': 'can_delete',
            'can_export': 'can_export',
        }

        user = request.user

        # Superuser: Full access
        if user.is_superuser:
            return True

        if user.is_staff:
            if accessType not in user_permissions:
                return False

            return UserPermission.objects.filter(
                user=user,
                is_active=True,
                menu__menu_url=view_name,
                **{user_permissions[accessType]: True}
            ).exists()

        return False

    except Exception as e:
        print("Permission check error:", e)
        return False
