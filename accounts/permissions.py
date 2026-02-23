"""
JeyaRamaDesk — Custom Permissions for RBAC
"""

from rest_framework.permissions import BasePermission


class IsSuperAdmin(BasePermission):
    """Only SuperAdmin users."""
    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == 'superadmin'
        )


class IsManager(BasePermission):
    """SuperAdmin or Manager."""
    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role in ('superadmin', 'manager')
        )


class IsAgent(BasePermission):
    """SuperAdmin, Manager, or Agent."""
    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role in ('superadmin', 'manager', 'agent')
        )


class IsStaffMember(BasePermission):
    """Any internal staff (not customer)."""
    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.is_staff_member
        )


class IsCustomer(BasePermission):
    """Only Customer role."""
    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == 'customer'
        )


class IsOwnerOrStaff(BasePermission):
    """Object-level: owner or staff member."""
    def has_object_permission(self, request, view, obj):
        if request.user.is_staff_member:
            return True
        # Check common owner fields
        if hasattr(obj, 'customer'):
            return obj.customer == request.user
        if hasattr(obj, 'user'):
            return obj.user == request.user
        if hasattr(obj, 'created_by'):
            return obj.created_by == request.user
        return False
