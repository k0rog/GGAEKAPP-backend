from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group
from django.contrib.auth.models import Permission

my_apps = ['users']

# value is a model name
PERMISSION_CONFIG = {
    'headmaster': {
        'full': ['staff', 'teacher', 'student', 'subject',
                 'StudentGroup', 'speciality', 'year', 'curriculum', 'StudentGroup_Curriculum'
                 ],
        'view': [],
        'add': [],
        'change': [],
        'delete': [],
    },
    'deputy': {
        'full': ['staff'],
        'view': [],
        'add': [],
        'change': [],
        'delete': [],
    },
    'department_head': {
        'full': ['teacher', 'studentgroup'],
        'view': [],
        'add': [],
        'change': [],
        'delete': [],
    },
    'teacher': {
        'full': ['student', 'ArticleFile', 'Article'],
        'view': [],
        'add': [],
        'change': [],
        'delete': [],
    },
}


class Command(BaseCommand):
    def handle(self, *args, **options):
        headmaster_group, _ = Group.objects.get_or_create(name='headmaster')
        deputy_group, _ = Group.objects.get_or_create(name='deputy')
        department_head_group, _ = Group.objects.get_or_create(name='department_head')
        teacher_group, _ = Group.objects.get_or_create(name='teacher')
        student_group, _ = Group.objects.get_or_create(name='student')

        groups = Group.objects.all()
        for group in groups:
            # check is group in config
            try:
                config = PERMISSION_CONFIG[group.name]
            except KeyError:
                continue

            permission_codenames = []

            if 'full' in config:
                for model in config['full']:
                    permission_codenames += [f'{perm_type}_{model.lower()}'
                                             for perm_type in ['view', 'change', 'delete', 'add']]

            for perm_type in config:
                if perm_type != 'full':
                    for model in config[perm_type]:
                        permission_codenames.append(f'{perm_type}_{model.lower()}')

            permissions = Permission.objects.filter(codename__in=permission_codenames)

            # if there is any difference between configured and possible permissions command will notify you
            if permissions.count() != len(permission_codenames):
                not_found_permissions = set(permission_codenames).difference(set([permission.codename
                                                                                  for permission in permissions]))

                found_permissions = set([permission.codename
                                         for permission in permissions]).intersection(set(permission_codenames))

                if len(found_permissions):
                    success_text = f'Added permissions: {", ".join(found_permissions)} for group {group.name}'
                    self.stdout.write(self.style.SUCCESS(success_text))

                warning_text = f'Not found permissions: {", ".join(not_found_permissions)} for group {group.name}'
                self.stdout.write(self.style.WARNING(warning_text))

            group.permissions.add(*permissions)
