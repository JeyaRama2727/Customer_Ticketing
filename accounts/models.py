"""
JeyaRamaDesk — Accounts Models
Custom User model with Role-Based Access Control (RBAC).
Designed for millions of records with proper indexing.
"""

from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.db import models
from django.utils import timezone
import uuid


class UserManager(BaseUserManager):
    """Custom manager for the User model."""

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Email address is required.')
        email = self.normalize_email(email)
        extra_fields.setdefault('role', User.Role.CUSTOMER)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', User.Role.SUPERADMIN)
        if not extra_fields.get('is_staff'):
            raise ValueError('Superuser must have is_staff=True.')
        if not extra_fields.get('is_superuser'):
            raise ValueError('Superuser must have is_superuser=True.')
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """
    Custom User model for JeyaRamaDesk.
    Uses email as the unique identifier instead of username.
    """

    class Role(models.TextChoices):
        SUPERADMIN = 'superadmin', 'Super Admin'
        MANAGER = 'manager', 'Manager'
        AGENT = 'agent', 'Agent'
        CUSTOMER = 'customer', 'Customer'

    # ── Identity ──────────────────────────────────────────────
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField('Email Address', unique=True, db_index=True)
    first_name = models.CharField('First Name', max_length=150)
    last_name = models.CharField('Last Name', max_length=150)
    phone = models.CharField('Phone Number', max_length=20, blank=True, default='')
    address = models.TextField('Address', blank=True, default='')
    avatar = models.ImageField(
        'Profile Picture',
        upload_to='avatars/%Y/%m/',
        blank=True,
        null=True,
    )

    # ── Role & Permissions ────────────────────────────────────
    role = models.CharField(
        'Role',
        max_length=20,
        choices=Role.choices,
        default=Role.CUSTOMER,
        db_index=True,
    )
    department = models.CharField(max_length=100, blank=True, default='')
    job_title = models.CharField(max_length=100, blank=True, default='')

    # ── Status ────────────────────────────────────────────────
    is_active = models.BooleanField('Active', default=True, db_index=True)
    is_staff = models.BooleanField('Staff Status', default=False)
    is_online = models.BooleanField('Online', default=False)
    is_profile_completed = models.BooleanField('Profile Completed', default=False)

    # ── Timestamps ────────────────────────────────────────────
    date_joined = models.DateTimeField('Date Joined', default=timezone.now)
    last_login = models.DateTimeField('Last Login', blank=True, null=True)
    updated_at = models.DateTimeField('Updated At', auto_now=True)

    # ── Preferences ───────────────────────────────────────────
    timezone_pref = models.CharField(
        'Timezone', max_length=50, default='UTC',
    )
    email_notifications = models.BooleanField(default=True)
    dark_mode = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    class Meta:
        db_table = 'jrd_users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        ordering = ['-date_joined']
        indexes = [
            models.Index(fields=['role', 'is_active'], name='idx_user_role_active'),
            models.Index(fields=['email'], name='idx_user_email'),
            models.Index(fields=['date_joined'], name='idx_user_joined'),
        ]

    def __str__(self):
        return f'{self.full_name} ({self.email})'

    @property
    def full_name(self):
        return f'{self.first_name} {self.last_name}'.strip()

    @property
    def initials(self):
        return f'{self.first_name[:1]}{self.last_name[:1]}'.upper()

    @property
    def is_superadmin(self):
        return self.role == self.Role.SUPERADMIN

    @property
    def is_manager(self):
        return self.role == self.Role.MANAGER

    @property
    def is_agent(self):
        return self.role == self.Role.AGENT

    @property
    def is_customer(self):
        return self.role == self.Role.CUSTOMER

    @property
    def is_staff_member(self):
        """Returns True for superadmin, manager, or agent."""
        return self.role in (self.Role.SUPERADMIN, self.Role.MANAGER, self.Role.AGENT)


class LoginAuditLog(models.Model):
    """Tracks all login attempts for security auditing."""

    class Status(models.TextChoices):
        SUCCESS = 'success', 'Success'
        FAILED = 'failed', 'Failed'
        LOCKED = 'locked', 'Account Locked'

    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='login_logs',
    )
    email_attempted = models.EmailField(db_index=True)
    status = models.CharField(max_length=10, choices=Status.choices)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True, default='')
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = 'jrd_login_audit'
        ordering = ['-timestamp']
        indexes = [
            models.Index(
                fields=['email_attempted', 'timestamp'],
                name='idx_login_email_time',
            ),
            models.Index(
                fields=['ip_address', 'timestamp'],
                name='idx_login_ip_time',
            ),
        ]

    def __str__(self):
        return f'{self.email_attempted} — {self.status} at {self.timestamp}'
