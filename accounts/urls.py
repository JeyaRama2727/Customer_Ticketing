"""
JeyaRamaDesk — Accounts URL Configuration
"""

from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    # Authentication
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),

    # Profile
    path('profile/', views.profile_view, name='profile'),
    path('complete-profile/', views.complete_profile_view, name='complete_profile'),
    path('change-password/', views.change_password_view, name='change_password'),

    # User management (staff)
    path('users/', views.user_list_view, name='user_list'),
    path('users/create/', views.user_create_view, name='user_create'),
    path('users/<uuid:pk>/edit/', views.user_edit_view, name='user_edit'),
    path('users/<uuid:pk>/toggle/', views.user_toggle_active_view, name='user_toggle_active'),

    # Audit logs
    path('audit-logs/', views.audit_log_view, name='audit_log'),
]
