from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    path('dashboard/', views.dashboard_view, name='dashboard'),

    path('dashboard/staff/users/', views.all_user_list_view, name='all_user_list'),
    path('dashboard/staff/activity/', views.user_activity_list, name='user_activity_list'),
    path('dashboard/staff/access-logs/', views.user_access_log_list, name='user_access_log_list'),
    path('dashboard/staff/users/<int:user_id>/', views.user_detail_view, name='user_detail'),
    path('dashboard/staff/users/<int:user_id>/status/', views.toggle_user_status, name='toggle_user_status'),
    
]