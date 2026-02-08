from rest_framework import permissions

class IsAdmin(permissions.BasePermission):
    """
    Custom permission to only allow administrators to access the view.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role == 'ADMIN'

class IsHODOrAdmin(permissions.BasePermission):
    """
    Custom permission to allow HODs and Admins.
    HODs are restricted to their own department (handled in view filters).
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and (
            request.user.role == 'ADMIN' or request.user.role == 'HOD'
        )

class IsFacultyOrAbove(permissions.BasePermission):
    """
    Custom permission to allow Faculty, HODs, and Admins.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and (
            request.user.role in ['ADMIN', 'HOD', 'FACULTY']
        )
