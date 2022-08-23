from rest_framework import permissions
from django.utils.translation import gettext_lazy as _
from .models import Teacher


class IsOwner(permissions.BasePermission):
    message = _('This action is only for profile owners')

    def has_permission(self, request, view):
        if view.kwargs['user_id'] == request.user.id:
            return True

        return False


class IsTeacher(permissions.BasePermission):
    message = _('This action is only for teachers')

    def has_permission(self, request, view):
        if Teacher.objects.filter(pk=request.user.id).exists():
            return True

        return False
