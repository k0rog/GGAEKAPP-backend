from django.utils.translation import gettext_lazy as _


class AdminReallyDeleteActionMixin:
    actions = ['really_delete_selected']

    def get_actions(self, request):
        actions = super().get_actions(request)
        del actions['delete_selected']
        return actions

    def really_delete_selected(self, request, queryset):
        for obj in queryset:
            obj.delete()

        if queryset.count() == 1:
            message_bit = _(f'1 {self.model._meta.verbose_name} entry was')
        else:
            message_bit = _(f'{queryset.count()} {self.model._meta.verbose_name_plural} entries were')
        self.message_user(request, _(f'{message_bit} successfully deleted'))
    really_delete_selected.short_description = _('Delete selected entries')
