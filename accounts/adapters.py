"""
JeyaRamaDesk — Allauth Adapters
Custom adapters to integrate django-allauth with our custom User model.
Ensures Google-authenticated users are created with the 'customer' role.
"""

from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.urls import reverse

class AccountAdapter(DefaultAccountAdapter):
    """Override default allauth account behaviour."""

    def save_user(self, request, user, form, commit=True):
        """Ensure regular signups default to the customer role."""
        user = super().save_user(request, user, form, commit=False)
        user.role = 'customer'
        if commit:
            user.save()
        return user

    def get_login_redirect_url(self, request):
        """
        After login, redirect to profile completion if the user
        has not yet filled in their details.
        """
        user = request.user
        return super().get_login_redirect_url(request)


class SocialAccountAdapter(DefaultSocialAccountAdapter):
    """
    Custom adapter for social (Google) logins.
    Automatically assigns the 'customer' role and populates profile fields.
    """

    def pre_social_login(self, request, sociallogin):
        """
        If a user with the same email already exists, connect the
        social account to that existing user instead of creating a duplicate.
        """
        if sociallogin.is_existing:
            return

        email = sociallogin.account.extra_data.get('email')
        if email:
            from accounts.models import User
            try:
                existing_user = User.objects.get(email=email)
                sociallogin.connect(request, existing_user)
            except User.DoesNotExist:
                pass

    def save_user(self, request, sociallogin, form=None):
        """
        Populate custom fields from the Google profile data and
        assign the customer role. Mark profile as NOT completed
        so the user is redirected to the completion form.
        """
        user = super().save_user(request, sociallogin, form)
        data = sociallogin.account.extra_data

        user.role = 'customer'
        user.first_name = data.get('given_name', user.first_name or '')
        user.last_name = data.get('family_name', user.last_name or '')
        user.is_profile_completed = True  # Force profile completion
        user.save(update_fields=['role', 'first_name', 'last_name', 'is_profile_completed'])
        return user

    def populate_user(self, request, sociallogin, data):
        """Set initial field values before the user is saved."""
        user = super().populate_user(request, sociallogin, data)
        user.role = 'customer'
        return user
