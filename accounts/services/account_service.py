"""
JeyaRamaDesk — Accounts Service Layer
Business logic for user management and authentication.
"""

import logging
from django.contrib.auth import authenticate, login, logout
from django.db import transaction
from accounts.models import User, LoginAuditLog

logger = logging.getLogger('jeyaramadesk')


class AuthService:
    """Handles authentication business logic."""

    @staticmethod
    def login_user(request, email, password):
        """
        Authenticate and login a user.
        Returns (user, error_message) tuple.
        """
        ip = AuthService._get_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')

        user = authenticate(request, username=email, password=password)

        if user is None:
            # Log failed attempt
            LoginAuditLog.objects.create(
                email_attempted=email,
                status=LoginAuditLog.Status.FAILED,
                ip_address=ip,
                user_agent=user_agent,
            )
            logger.warning(f'Failed login attempt for {email} from {ip}')
            return None, 'Invalid email or password.'

        if not user.is_active:
            LoginAuditLog.objects.create(
                user=user,
                email_attempted=email,
                status=LoginAuditLog.Status.LOCKED,
                ip_address=ip,
                user_agent=user_agent,
            )
            return None, 'Your account is deactivated. Contact support.'

        # Success
        login(request, user)
        LoginAuditLog.objects.create(
            user=user,
            email_attempted=email,
            status=LoginAuditLog.Status.SUCCESS,
            ip_address=ip,
            user_agent=user_agent,
        )
        user.is_online = True
        user.save(update_fields=['is_online', 'last_login'])
        logger.info(f'User {email} logged in from {ip}')
        return user, None

    @staticmethod
    def logout_user(request):
        """Logout the current user."""
        if request.user.is_authenticated:
            request.user.is_online = False
            request.user.save(update_fields=['is_online'])
        logout(request)

    @staticmethod
    def _get_ip(request):
        xff = request.META.get('HTTP_X_FORWARDED_FOR')
        if xff:
            return xff.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', '0.0.0.0')


class UserService:
    """Business logic for user CRUD operations."""

    @staticmethod
    @transaction.atomic
    def create_user(data):
        """Create a new user with validated data."""
        user = User.objects.create_user(
            email=data['email'],
            password=data['password'],
            first_name=data.get('first_name', ''),
            last_name=data.get('last_name', ''),
            role=data.get('role', User.Role.CUSTOMER),
            phone=data.get('phone', ''),
            department=data.get('department', ''),
            job_title=data.get('job_title', ''),
        )
        logger.info(f'New user created: {user.email} ({user.role})')
        return user

    @staticmethod
    @transaction.atomic
    def update_user(user, data):
        """Update user profile fields."""
        updatable = [
            'first_name', 'last_name', 'phone',
            'department', 'job_title', 'timezone_pref',
            'email_notifications', 'dark_mode',
        ]
        updated_fields = []
        for field in updatable:
            if field in data:
                setattr(user, field, data[field])
                updated_fields.append(field)

        if updated_fields:
            user.save(update_fields=updated_fields + ['updated_at'])
        return user

    @staticmethod
    def get_agents():
        """Get all active agents."""
        return User.objects.filter(
            role__in=[User.Role.AGENT, User.Role.MANAGER, User.Role.SUPERADMIN],
            is_active=True,
        ).order_by('first_name')

    @staticmethod
    def get_customers():
        """Get all active customers."""
        return User.objects.filter(
            role=User.Role.CUSTOMER,
            is_active=True,
        ).order_by('first_name')

    @staticmethod
    def get_user_stats():
        """Return user count statistics."""
        from django.db.models import Count, Q
        return User.objects.aggregate(
            total=Count('id'),
            active=Count('id', filter=Q(is_active=True)),
            agents=Count('id', filter=Q(role=User.Role.AGENT, is_active=True)),
            customers=Count('id', filter=Q(role=User.Role.CUSTOMER, is_active=True)),
            online=Count('id', filter=Q(is_online=True)),
        )
