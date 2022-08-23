from rest_framework import permissions
from django.utils.translation import gettext_lazy as _
from chat.models import Chat


class IsChatMember(permissions.BasePermission):
    message = _('This action is only for chat members')

    def has_permission(self, request, view):
        chat_id = view.kwargs['chat_id']
        if Chat.objects.filter(users__in=[request.user.id], pk=chat_id).exists():
            return True

        return False
