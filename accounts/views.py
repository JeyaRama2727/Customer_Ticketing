"""
JeyaRamaDesk — Accounts Views (Template-based)
"""

import re
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import models
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator
from accounts.services.account_service import AuthService, UserService
from accounts.models import User, LoginAuditLog
from django.conf import settings

# ── Authentication Views ──────────────────────────────────────

def login_view(request):
    """Handle user login."""
    if request.user.is_authenticated:
        return redirect('dashboard:index')

    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        user, error = AuthService.login_user(request, email, password)

        if user:
            messages.success(request, f'Welcome back, {user.first_name}!')
            next_url = request.GET.get('next', settings.LOGIN_REDIRECT_URL)
            return redirect(next_url)
        else:
            messages.error(request, error)

    return render(request, 'accounts/login.html')


@login_required
def logout_view(request):
    """Handle user logout."""
    AuthService.logout_user(request)
    messages.info(request, 'You have been logged out.')
    return redirect('accounts:login')


def register_view(request):
    """Handle customer registration."""
    if request.user.is_authenticated:
        return redirect('dashboard:index')

    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        confirm = request.POST.get('confirm_password', '')
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()

        # Validation
        errors = []
        if not email or not password or not first_name:
            errors.append('All required fields must be filled.')
        if password != confirm:
            errors.append('Passwords do not match.')
        if len(password) < 10:
            errors.append('Password must be at least 10 characters.')
        if User.objects.filter(email=email).exists():
            errors.append('An account with this email already exists.')

        if errors:
            for e in errors:
                messages.error(request, e)
        else:
            UserService.create_user({
                'email': email,
                'password': password,
                'first_name': first_name,
                'last_name': last_name,
                'role': User.Role.CUSTOMER,
            })
            messages.success(request, 'Account created! Please log in.')
            return redirect('accounts:login')

    return render(request, 'accounts/register.html')


# ── Profile Views ─────────────────────────────────────────────

@login_required
def profile_view(request):
    """User profile page."""
    if request.method == 'POST':
        data = {
            'first_name': request.POST.get('first_name', '').strip(),
            'last_name': request.POST.get('last_name', '').strip(),
            'phone': request.POST.get('phone', '').strip(),
            'department': request.POST.get('department', '').strip(),
            'job_title': request.POST.get('job_title', '').strip(),
            'timezone_pref': request.POST.get('timezone_pref', 'UTC'),
            'email_notifications': request.POST.get('email_notifications') == 'on',
            'dark_mode': request.POST.get('dark_mode') == 'on',
        }

        # Handle avatar upload
        if 'avatar' in request.FILES:
            request.user.avatar = request.FILES['avatar']
            request.user.save(update_fields=['avatar'])

        UserService.update_user(request.user, data)
        messages.success(request, 'Profile updated successfully.')
        return redirect('accounts:profile')

    return render(request, 'accounts/profile.html')


@login_required
def change_password_view(request):
    """Change password."""
    if request.method == 'POST':
        current = request.POST.get('current_password', '')
        new_pw = request.POST.get('new_password', '')
        confirm = request.POST.get('confirm_password', '')

        if not request.user.check_password(current):
            messages.error(request, 'Current password is incorrect.')
        elif new_pw != confirm:
            messages.error(request, 'New passwords do not match.')
        elif len(new_pw) < 10:
            messages.error(request, 'Password must be at least 10 characters.')
        else:
            request.user.set_password(new_pw)
            request.user.save()
            messages.success(request, 'Password changed. Please log in again.')
            return redirect('accounts:login')

    return render(request, 'accounts/change_password.html')


# ── Profile Completion (Google OAuth) ─────────────────────────

@login_required
def complete_profile_view(request):
    """
    Force first-time Google users to provide name, phone, and address.
    Phone is optional but must be exactly 10 digits if provided.
    """
    user = request.user

    # Already completed — skip straight to dashboard
    if user.is_profile_completed:
        return redirect('dashboard:index')

    if request.method == 'POST':
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        phone = request.POST.get('phone', '').strip()
        address = request.POST.get('address', '').strip()

        errors = []

        # Name is mandatory
        if not first_name:
            errors.append('First name is required.')
        if not last_name:
            errors.append('Last name is required.')

        # Phone is optional, but if provided must be exactly 10 digits
        if phone:
            digits_only = re.sub(r'\D', '', phone)   # strip non-digit chars
            if len(digits_only) != 10:
                errors.append('Phone number must be exactly 10 digits.')
            else:
                phone = digits_only  # store clean digits only

        if errors:
            for e in errors:
                messages.error(request, e)
            return render(request, 'accounts/complete_profile.html', {
                'first_name': first_name,
                'last_name': last_name,
                'phone': phone,
                'address': address,
            })

        # Save profile data and mark as completed
        user.first_name = first_name
        user.last_name = last_name
        user.phone = phone
        user.address = address
        user.is_profile_completed = True
        user.save(update_fields=[
            'first_name', 'last_name', 'phone', 'address', 'is_profile_completed',
        ])

        messages.success(request, 'Profile completed! Welcome to JeyaRamaDesk.')
        return redirect('dashboard:index')

    # GET — pre-fill with any data Google already provided
    return render(request, 'accounts/complete_profile.html', {
        'first_name': user.first_name,
        'last_name': user.last_name,
        'phone': user.phone,
        'address': user.address,
    })


# ── User Management (Admin/Manager) ──────────────────────────

@login_required
def user_list_view(request):
    """List all users (staff only)."""
    if not request.user.is_staff_member:
        messages.error(request, 'Permission denied.')
        return redirect('dashboard:index')

    users = User.objects.all().order_by('-date_joined')

    # Filters
    role_filter = request.GET.get('role', '')
    status_filter = request.GET.get('status', '')
    search = request.GET.get('search', '')

    if role_filter:
        users = users.filter(role=role_filter)
    if status_filter == 'active':
        users = users.filter(is_active=True)
    elif status_filter == 'inactive':
        users = users.filter(is_active=False)
    if search:
        users = users.filter(
            models.Q(email__icontains=search)
            | models.Q(first_name__icontains=search)
            | models.Q(last_name__icontains=search)
        )

    paginator = Paginator(users, 25)
    page = request.GET.get('page')
    users_page = paginator.get_page(page)

    return render(request, 'accounts/user_list.html', {
        'users': users_page,
        'role_filter': role_filter,
        'status_filter': status_filter,
        'search': search,
        'roles': User.Role.choices,
    })


@login_required
def user_create_view(request):
    """Create a new user (manager+ only)."""
    if request.user.role not in (User.Role.SUPERADMIN, User.Role.MANAGER):
        messages.error(request, 'Permission denied.')
        return redirect('accounts:user_list')

    if request.method == 'POST':
        data = {
            'email': request.POST.get('email', '').strip(),
            'password': request.POST.get('password', ''),
            'first_name': request.POST.get('first_name', '').strip(),
            'last_name': request.POST.get('last_name', '').strip(),
            'role': request.POST.get('role', User.Role.CUSTOMER),
            'phone': request.POST.get('phone', '').strip(),
            'department': request.POST.get('department', '').strip(),
            'job_title': request.POST.get('job_title', '').strip(),
        }

        if User.objects.filter(email=data['email']).exists():
            messages.error(request, 'Email already exists.')
        else:
            UserService.create_user(data)
            messages.success(request, f'User {data["email"]} created.')
            return redirect('accounts:user_list')

    return render(request, 'accounts/user_form.html', {
        'roles': User.Role.choices,
        'action': 'Create',
    })


@login_required
def user_edit_view(request, pk):
    """Edit a user (manager+ only)."""
    if request.user.role not in (User.Role.SUPERADMIN, User.Role.MANAGER):
        messages.error(request, 'Permission denied.')
        return redirect('accounts:user_list')

    user_obj = get_object_or_404(User, pk=pk)

    if request.method == 'POST':
        data = {
            'first_name': request.POST.get('first_name', '').strip(),
            'last_name': request.POST.get('last_name', '').strip(),
            'phone': request.POST.get('phone', '').strip(),
            'department': request.POST.get('department', '').strip(),
            'job_title': request.POST.get('job_title', '').strip(),
        }
        # Role change only by superadmin
        if request.user.is_superadmin:
            new_role = request.POST.get('role', user_obj.role)
            user_obj.role = new_role
            user_obj.save(update_fields=['role'])

        UserService.update_user(user_obj, data)
        messages.success(request, 'User updated.')
        return redirect('accounts:user_list')

    return render(request, 'accounts/user_form.html', {
        'user_obj': user_obj,
        'roles': User.Role.choices,
        'action': 'Edit',
    })


@login_required
@require_http_methods(['POST'])
def user_toggle_active_view(request, pk):
    """Toggle user active status."""
    if request.user.role not in (User.Role.SUPERADMIN, User.Role.MANAGER):
        messages.error(request, 'Permission denied.')
        return redirect('accounts:user_list')

    user_obj = get_object_or_404(User, pk=pk)
    user_obj.is_active = not user_obj.is_active
    user_obj.save(update_fields=['is_active'])
    status_txt = 'activated' if user_obj.is_active else 'deactivated'
    messages.success(request, f'User {user_obj.email} {status_txt}.')
    return redirect('accounts:user_list')


@login_required
def audit_log_view(request):
    """View login audit logs (superadmin only)."""
    if not request.user.is_superadmin:
        messages.error(request, 'Permission denied.')
        return redirect('dashboard:index')

    logs = LoginAuditLog.objects.select_related('user').all()
    paginator = Paginator(logs, 50)
    page = request.GET.get('page')
    logs_page = paginator.get_page(page)

    return render(request, 'accounts/audit_log.html', {'logs': logs_page})
