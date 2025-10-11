from django.shortcuts import render
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.shortcuts import redirect
from django.contrib.auth.models import User
from .models import Profile, UserActivity, UserAccessLog
from django.utils.timezone import now
from django.db.models import Q
from django.http import HttpResponseRedirect



# Create your views here.
def register_view(request):
    username = request.POST.get('username', '').strip()
    phone = request.POST.get('phone', '').strip()
    password1 = request.POST.get('password1')
    confirm2 = request.POST.get('password2')

    if request.method == 'POST':
        if not phone:
            return render(request, 'accounts/register.html', {'error': 'Please enter your phone number'})
        if not username:
            return render(request, 'accounts/register.html', {'error': 'Please enter a username'})
        if not password1:
            return render(request, 'accounts/register.html', {'error': 'Please enter a password'})
        if password1 != confirm2:
            return render(request, 'accounts/register.html', {'error': 'Passwords do not match'})
        if len(username) < 3:
            return render(request, 'accounts/register.html', {'error': 'Username must be at least 3 characters long'})
        if len(password1) < 8:
            return render(request, 'accounts/register.html', {'error': 'Password must be at least 8 characters long'})

        user = User.objects.create_user(username=username, password=password1)
        profile = Profile.objects.create(user=user, phone=phone)
        profile.save()
        user.save()
        login(request, user)
        messages.success(request, 'Registration successful')
        return redirect('accounts:dashboard')
        
    return render(request, 'accounts/register.html')


def login_view(request):
    if request.method == 'POST':
        phone = request.POST.get('phone')
        password = request.POST.get('password')

        profile = Profile.objects.get(phone=phone)
        username = profile.user.username
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            next_url = request.GET.get('next')
            if next_url:
                next_url = next_url.strip()
            else:
                next_url = 'accounts:dashboard'
            messages.success(request, 'Login successful')
            return redirect('accounts:dashboard')
        else:
            messages.error(request, 'Invalid username or password')
            return render(request, 'accounts/login.html')

    return render(request, 'accounts/login.html')

def logout_view(request):
    logout(request)
    messages.success(request, 'Logout successful')
    return redirect('accounts:login')

def dashboard_view(request):
    return render(request, 'accounts/dashboard.html')


def all_user_list_view(request):
    searchQ = request.GET.get('search')
    roleQ = request.GET.get('role', '')

    users = User.objects.all()

    if searchQ:
        users = users.filter(
            Q(username__icontains=searchQ) |
            Q(first_name__icontains=searchQ) |
            Q(last_name__icontains=searchQ) |
            Q(email__icontains=searchQ) |
            Q(profile__phone__icontains=searchQ)
        )

    if roleQ == 'superadmin':
        users = users.filter(is_superuser=True)
    elif roleQ == 'staff':
        users = users.filter(is_staff=True, is_superuser=False)
    elif roleQ == 'customer':
        users = users.filter(is_staff=False, is_superuser=False)



    context = {
        'users': users,
        'searchQ': searchQ,
        'roleQ': roleQ,
    }
    return render(request, 'accounts/users/all_user_list.html', context)

def user_activity_list(request):
    activities = UserActivity.objects.select_related('user').all()
    return render(request, 'accounts/users/user_activity_list.html', {
        'activities': activities,
        'now': now(),  # ✅ Pass current time to the template
    })



def user_access_log_list(request):
    logs = UserAccessLog.objects.select_related('user').order_by('-login_time')[:100]
    return render(request, 'accounts/users/user_access_log_list.html', {
        'logs': logs
    })

def user_detail_view(request, user_id):
    user = User.objects.get(id=user_id)
    return render(request, 'accounts/users/user_detail.html', {
        'user': user
    })

def toggle_user_status(request, user_id):
    user = User.objects.get(id=user_id)
    user.is_active = not user.is_active
    user.save()
    refer_page = request.META.get('HTTP_REFERER')
    if refer_page:
        return HttpResponseRedirect(refer_page)
    return redirect('accounts:all_user_list')