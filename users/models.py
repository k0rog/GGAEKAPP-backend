from hashlib import sha256
from django.utils.translation import gettext_lazy as _
from django.db import models
from django.contrib.auth.models import AbstractUser, Group
from college.utils.picture_generator import generate_picture
from college.utils import aws_supplier, file_cleaner
from django.conf import settings
from django.core.files.images import ImageFile
from django.core.validators import RegexValidator
from django.core.mail import send_mail


ALLOWED_GROUPS = {
    'headmaster': ['headmaster', 'department_head', 'deputy'],
    'department_head': ['teacher'],
    'teacher': ['student']
}


def get_avatar_path(self, filename):
    return f'{self.email}/{filename}'


class User(AbstractUser):
    phone_regex = RegexValidator(regex=r'^\+?1?\d{9,15}$',
                                 message="Phone number must be entered in the format: "
                                         "'+999999999'. Up to 15 digits allowed.")
    username = None
    phone_number = models.CharField(validators=[phone_regex], max_length=17, verbose_name=_('phone_number'))
    email = models.CharField(max_length=255, unique=True, verbose_name=_('email'))
    avatar = models.ImageField(upload_to=get_avatar_path, null=True, default=None, verbose_name=_('avatar'))
    first_name = models.CharField(max_length=255, null=False, verbose_name=_('first_name'))
    last_name = models.CharField(max_length=255, null=False, verbose_name=_('last_name'))
    phone_publicity = models.BooleanField(default=True, verbose_name=_('phone_publicity'))
    temporary_password = models.BooleanField(default=True, verbose_name=_('temporary_password'))

    def __init__(self, *args, create_avatar=True, **kwargs):
        super().__init__(*args, **kwargs)
        self._previous_email = self.email
        self.create_avatar = create_avatar
        self.previous_avatar = self.avatar

    def __str__(self):
        if self.first_name and self.last_name:
            return f'{self.first_name}, {self.last_name}'
        else:
            return self.email

    def generate_avatar(self):
        initials = f'{self.first_name[0].upper()}{self.last_name[0].upper()}'
        media_url = settings.MEDIA_URL.lstrip("/")
        filename = f"{initials}.jpeg"
        avatar_path = get_avatar_path(self, filename)

        picture = generate_picture(initials)

        if settings.REMOTE_FILE_STORAGE:
            aws_supplier.send_file(picture, f'{media_url}{avatar_path}')
            self.avatar = avatar_path
        else:
            self.avatar = ImageFile(picture, name=filename)

    def save(self, *args, **kwargs):
        if not self._previous_email and not User.objects.filter(email=self.email).exists():
            # User is not able to register at app. User gets created at the admin panel by the other user with higher
            # permission group at the hierarchy
            temp_password = sha256(self.email.encode('utf-8')).hexdigest()
            self.set_password(temp_password)

            send_mail(
                _('Your temporary password for GGAEK app'),
                temp_password,
                from_email=None,
                recipient_list=[self.email],
                fail_silently=False
            )
            # self.set_password(self.email)

        if self.previous_avatar != self.avatar:
            file_cleaner.delete_assigned_file(self.previous_avatar)

        if not self.avatar and self.first_name and self.last_name and self.create_avatar:
            self.generate_avatar()

        return super().save(*args, **kwargs)

    def get_allowed_groups(self):
        if self.groups.first().name in ALLOWED_GROUPS:
            return Group.objects.filter(name__in=ALLOWED_GROUPS[self.groups.first().name])
        return Group.objects.all()

    def delete(self, using=None, keep_parents=False):
        file_cleaner.delete_assigned_file(self.avatar)
        return super().delete(using, keep_parents)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []


class Student(User):
    group = models.ForeignKey('college.StudentGroup', related_name='students',
                              on_delete=models.CASCADE)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        student_group = Group.objects.get(name='student')
        self.groups.add(student_group)

    class Meta:
        verbose_name = _('Student')
        verbose_name_plural = _('Students')


class Teacher(User):
    subjects = models.ManyToManyField('college.Subject', related_name='teachers', verbose_name=_('subjects'))

    def save(self, *args, **kwargs):
        self.is_staff = True
        super().save(*args, **kwargs)
        teacher_group = Group.objects.get(name='teacher')
        self.groups.add(teacher_group)

    class Meta:
        verbose_name = _('Teacher')
        verbose_name_plural = _('Teachers')


class Staff(User):
    class Meta:
        verbose_name = _('Staff person')
        verbose_name_plural = _('Staff')


class EmailVerification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    EMAIL = 'E'
    PASSWORD = 'P'

    VERIFICATION_TYPES = (
        (EMAIL, _('Email')),
        (PASSWORD, _('Password')),
    )

    verification_type = models.CharField(choices=VERIFICATION_TYPES, max_length=2)
    code = models.IntegerField()
    done = models.BooleanField(default=False)
    new_value = models.CharField(max_length=255, null=True)
