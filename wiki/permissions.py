from rest_framework import permissions
from django.utils.translation import gettext_lazy as _
from users.models import Teacher


class IsArticleOwner(permissions.BasePermission):
    message = _('This action is only for article owners')

    def has_permission(self, request, view):
        teacher = Teacher.objects.get(pk=request.user.id)

        if teacher.articles.filter(pk=view.kwargs['pk']).exists():
            return True

        return False
