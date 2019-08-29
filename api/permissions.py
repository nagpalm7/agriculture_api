from rest_framework import permissions
from  .models import *

class IsAuthenticated(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.
    """
    def has_permission(self, request, view):

        if request.user.is_authenticated:
            return True
        return False