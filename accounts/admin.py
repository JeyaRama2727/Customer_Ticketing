"""
JeyaRamaDesk — Accounts Admin Configuration
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, LoginAuditLog


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Enhanced admin for the custom User model."""

    list_display = (
        'email', 'full_name', 'role', 'is_active',
        'is_staff', 'date_joined',
    )
    list_filter = ('role', 'is_active', 'is_staff', 'date_joined')
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('-date_joined',)
    list_per_page = 25

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {
            'fields': ('first_name', 'last_name', 'phone', 'avatar'),
        }),
        ('Role & Organization', {
            'fields': ('role', 'department', 'job_title'),
        }),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
            'classes': ('collapse',),
        }),
        ('Preferences', {
            'fields': ('timezone_pref', 'email_notifications', 'dark_mode'),
            'classes': ('collapse',),
        }),
        ('Important Dates', {
            'fields': ('last_login', 'date_joined'),
        }),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'email', 'first_name', 'last_name', 'role',
                'password1', 'password2',
            ),
        }),
    )

    actions = ['activate_users', 'deactivate_users']

    @admin.action(description='Activate selected users')
    def activate_users(self, request, queryset):
        queryset.update(is_active=True)

    @admin.action(description='Deactivate selected users')
    def deactivate_users(self, request, queryset):
        queryset.update(is_active=False)


@admin.register(LoginAuditLog)
class LoginAuditLogAdmin(admin.ModelAdmin):
    list_display = ('email_attempted', 'status', 'ip_address', 'timestamp')
    list_filter = ('status', 'timestamp')
    search_fields = ('email_attempted', 'ip_address')
    readonly_fields = (
        'user', 'email_attempted', 'status',
        'ip_address', 'user_agent', 'timestamp',
    )
    ordering = ('-timestamp',)
    list_per_page = 50
