from rest_framework.permissions import BasePermission

class UserTypePermission(BasePermission):
    def __init__(self, allowed_user_types):
        self.allowed_user_types = allowed_user_types
    def has_permission(self, request, view):
        if not request.user or not hasattr(request.user, 'user_type'):
            return False
        return request.user.user_type in self.allowed_user_types
    

class IsDonor(UserTypePermission):
    def __init__(self):
        super().__init__(allowed_user_types=['donor', 'both'])

class IsRecipient(UserTypePermission):
    def __init__(self):
        super().__init__(allowed_user_types=['recipient', 'both'])
class IsVerifiedUser(BasePermission):
    def has_permission(self, request, view):
        if not request.user or not hasattr(request.user, 'is_verified'):
            return False
        return request.user.is_verified
