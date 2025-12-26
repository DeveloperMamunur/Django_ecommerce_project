from accounts.models import Profile
from django.contrib.auth.models import User
from accounts.models import UserPermission
from .models import MenuList
from .permissions import CheckUserPermission
from products.models import Wishlist

def menu_permissions(request):
    if not request.user.is_authenticated:
        return {}

    user = request.user
    permissions = {}

    # Superuser gets everything
    if user.is_superuser:
        for menu in MenuList.objects.all():
            base = menu.menu_url.replace(":", "_")
            permissions[f'can_view_{base}'] = True
            permissions[f'can_create_{base}'] = True
            permissions[f'can_update_{base}'] = True
            permissions[f'can_delete_{base}'] = True
        return permissions

    # Staff: check permissions per menu
    for menu in MenuList.objects.all().values_list('menu_url', flat=True):
        base = menu.replace(":", "_")
        permissions[f'can_view_{base}'] = CheckUserPermission(request, 'can_view', menu)
        permissions[f'can_create_{base}'] = CheckUserPermission(request, 'can_create', menu)
        permissions[f'can_update_{base}'] = CheckUserPermission(request, 'can_update', menu)
        permissions[f'can_delete_{base}'] = CheckUserPermission(request, 'can_delete', menu)

    return permissions



def wishlist_counter(request):
    if request.user.is_authenticated:
        return {
            "wishlist_count": Wishlist.objects.filter(user=request.user).count()
        }
    return {"wishlist_count": 0}
