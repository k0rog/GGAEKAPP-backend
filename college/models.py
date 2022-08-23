from django.db import models
from users.models import Teacher
from django.utils.translation import gettext_lazy as _
from .validators import validate_start_year, validate_group_number
from chat.models import Chat


class Speciality(models.Model):
    title = models.CharField(max_length=255, verbose_name=_('title'))
    abbreviation = models.CharField(max_length=6, verbose_name=_('abbreviation'))
    group_prefix = models.CharField(max_length=3, verbose_name=_('group_prefix'))

    class Meta:
        verbose_name = _('Speciality')
        verbose_name_plural = _('Specialities')

    def __str__(self):
        return self.group_prefix


class Subject(models.Model):
    title = models.CharField(max_length=255, unique=True, verbose_name=_('title'))
    abbreviation = models.CharField(max_length=10, unique=True, verbose_name=_('abbreviation'))

    def __str__(self):
        return self.abbreviation

    class Meta:
        verbose_name = _('Subject')
        verbose_name_plural = _('Subjects')


FIRST_YEAR = 1
SECOND_YEAR = 2
THIRD_YEAR = 3
FOURTH_YEAR = 4

YEARS = (
    (FIRST_YEAR, _('First year')),
    (SECOND_YEAR, _('Second year')),
    (THIRD_YEAR, _('Third year')),
    (FOURTH_YEAR, _('Fourth year')),
)


class Year(models.Model):
    class Meta:
        unique_together = (('speciality', 'year', 'start_year'),)
        verbose_name = _('Year')
        verbose_name_plural = _('Years')

    speciality = models.ForeignKey(Speciality, on_delete=models.CASCADE, related_name='years',
                                   verbose_name=_('speciality'))
    year = models.IntegerField(choices=YEARS, verbose_name=_('year'))
    subjects = models.ManyToManyField(Subject, through='Curriculum', verbose_name=_('subjects'))
    start_year = models.IntegerField(validators=[validate_start_year], verbose_name=_('start_year'))

    def __str__(self):
        return f'{self.speciality}-{self.year}-{self.start_year}'


class Curriculum(models.Model):
    year = models.ForeignKey(Year, on_delete=models.CASCADE, verbose_name=_('year'), related_name='curriculums')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, verbose_name=_('subject'),
                                related_name='curriculums')

    class Meta:
        verbose_name = _('Curriculum')
        verbose_name_plural = _('Curriculums')

    def __str__(self):
        return f'{self.year}__{self.subject}'


class StudentGroup(models.Model):
    number = models.IntegerField(validators=[validate_group_number], verbose_name=_('number'))
    title = models.CharField(max_length=10, unique=True, verbose_name=_('title'))
    facilitator = models.OneToOneField(Teacher, on_delete=models.CASCADE, related_name='assigned_group',
                                       verbose_name=_('facilitator'))
    year = models.ForeignKey(Year, on_delete=models.CASCADE, verbose_name=_('year'))
    subjects = models.ManyToManyField(Curriculum, through='StudentGroup_Curriculum', related_name='student_groups',
                                      verbose_name=_('subjects'))

    class Meta:
        verbose_name = _('StudentGroup')
        verbose_name_plural = _('StudentGroups')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._previous_year = self.year if hasattr(self, 'year') else None

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        if not self.title:
            self.title = f'{self.year.speciality}-{self.year.year}{self.number}'

        if self.year != self._previous_year:
            self.delete_previous_year_chats()

        super().save(force_insert, force_update, using, update_fields)

    def delete_previous_year_chats(self):
        for through_instance in StudentGroup_Curriculum.objects.filter(student_group=self):
            subject_chat = Chat.objects.filter(
                title=f'{self.title}-{through_instance.curriculum.subject.abbreviation}'
            ).first()

            if subject_chat:
                subject_chat.delete()

    def update_group_chat(self):
        """ 1.Appends new students and facilitator to group chat
            2.Removes expelled students and old facilitator"""
        group_chat, created = Chat.objects.get_or_create(title=self.title)

        valid_members = list(self.students.all()) + [self.facilitator]

        group_chat.update_members(valid_members)

    def update_subject_chats(self):
        """ 1.Appends new students and teachers to all subject chats
            2.Removes expelled students and old teachers"""
        for through_instance in StudentGroup_Curriculum.objects.filter(student_group=self):
            subject_chat, changed = Chat.objects.get_or_create(
                title=f'{self.title}-{through_instance.curriculum.subject.abbreviation}'
            )

            valid_members = list(self.students.all()) + [through_instance.teacher]
            subject_chat.update_members(valid_members)

    def delete_assigned_chats(self):
        group_chat = Chat.objects.filter(title=self.title).first()
        if group_chat:
            group_chat.delete()

        for through_instance in StudentGroup_Curriculum.objects.filter(student_group=self):
            subject_chat = Chat.objects.filter(
                title=f'{self.title}-{through_instance.curriculum.subject.abbreviation}'
            ).first()
            if subject_chat:
                subject_chat.delete()

    def __str__(self):
        return self.title

    def delete(self, using=None, keep_parents=False):
        self.delete_assigned_chats()
        return super().delete(using, keep_parents)


class StudentGroup_Curriculum(models.Model):
    class Meta:
        unique_together = (('student_group', 'curriculum', 'teacher'),)
        verbose_name = _('StudentGroup_Curriculum')
        verbose_name_plural = _('StudentGroup_Curriculums')

    student_group = models.ForeignKey(StudentGroup, on_delete=models.CASCADE, verbose_name=_('student_group'))
    curriculum = models.ForeignKey(Curriculum, on_delete=models.CASCADE, verbose_name=_('curriculum'))
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, verbose_name=_('teacher'))
