from django.core.management import BaseCommand
from users.models import Staff
from django.contrib.auth.models import Group


class Command(BaseCommand):
    def handle(self, *args, **options):
        user, created = Staff.objects.get_or_create(email='ggaek@ggaek.by')
        if created:
            headmaster_group = Group.objects.get(name='headmaster')
            user.set_password('head')
            user.is_staff = True
            user.groups.add(headmaster_group)
            user.save()
