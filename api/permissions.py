from rest_framework.permissions import BasePermission, SAFE_METHODS

class IsSuperUserOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        # GET разрешен всем
        if request.method in SAFE_METHODS:
            return True

        # POST — только superuser
        return (
            request.user
            and request.user.is_authenticated
            and request.user.is_superuser
        )
