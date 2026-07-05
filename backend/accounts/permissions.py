from rest_framework.permissions import BasePermission


class IsPremiumOrStaff(BasePermission):
    """Allow access only to users with Premium access or staff status.

    Premium is managed in PRomop (Identity.is_premium) and is readable here
    because PRism and PRomop share the same PostgreSQL database and Identity table.
    """
    message = "Premium subscription required."

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return getattr(request.user, 'is_premium', False) or request.user.is_staff
