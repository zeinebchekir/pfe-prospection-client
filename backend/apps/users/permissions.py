"""
Custom DRF permission classes for role-based access control.

Currently implemented:
  IsAdmin  — ADMIN role only. Used for user management and audit log endpoints.

Not yet implemented (enforced at frontend routing level only):
  IsCEO        — would restrict CEO-specific API endpoints
  IsCommercial — would restrict commercial leads/opportunities endpoints

See SECURITY_NOTES.md for the implications of missing backend role enforcement.
"""
from rest_framework import permissions

class IsAdmin(permissions.BasePermission):
    """
    Autorise uniquement les utilisateurs avec le rôle ADMIN.
    """
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == 'ADMIN')
