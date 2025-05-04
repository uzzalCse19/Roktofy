from rest_framework.permissions import BasePermission

class CanRequestBlood(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        return user.is_authenticated and user.user_type in ['recipient', 'both'] and user.is_verified

class CanDonateBlood(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        return user.is_authenticated and user.user_type in ['donor', 'both'] and user.is_verified

