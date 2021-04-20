from rest_framework.permissions import (
    BasePermission,
    IsAuthenticatedOrReadOnly,
    SAFE_METHODS
)


class IsAdmin(BasePermission):
    """Проверка что пользователь является админом"""

    def has_permission(self, request, view):
        return (request.user.is_staff
                or request.user.is_superuser
                or request.user.is_admin)


class IsAdminOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        if request.user.is_authenticated:
            return request.user.is_staff or request.user.is_admin


class IsAdminOrModeratorOrOwnerOrReadOnly(IsAuthenticatedOrReadOnly):
    def has_object_permission(self, request, view, obj):
        return bool(
            obj.author == request.user
            or request.method in SAFE_METHODS
            or request.auth and request.user.is_admin
            or request.auth and request.user.is_moderator
        )
