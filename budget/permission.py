from rest_framework.permissions import BasePermission

class IsFinanceApprover(BasePermission):
    """
    Simple example: staff users or custom flag is_finance allowed.
    Replace with your project's role logic.
    """
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and (request.user.is_staff or getattr(request.user, "is_finance", False)))
