from rest_framework import permissions

class IsAdmin(permissions.BasePermission):
    """
    Autorise uniquement les utilisateurs avec le rôle ADMIN.
    """
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == 'ADMIN')
