from django.forms import BaseInlineFormSet
from college.models import StudentGroup_Curriculum, Curriculum
from django.contrib import admin
from users.models import Student, Teacher
from django.utils.translation import gettext_lazy as _


class StudentInline(admin.TabularInline):
    model = Student
    fields = ['email', 'first_name', 'last_name']
    extra = 1
    verbose_name = _('Student')
    verbose_name_plural = _('Students')


class SubjectInlineFormSet(BaseInlineFormSet):
    model = StudentGroup_Curriculum

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        curriculums = self.obj.year.curriculums.all()
        initial = [{'curriculum': curriculum} for curriculum in curriculums]
        #
        # teachers = [{'teacher': teacher} for teacher in
        #             Teacher.objects.filter(subjects__curriculums__in=curriculums).distinct()]
        # initial += teachers
        self.initial = initial


class SubjectInline(admin.TabularInline):
    model = StudentGroup_Curriculum
    fields = ['teacher', 'curriculum']
    formset = SubjectInlineFormSet
    extra = 0

    def get_formset(self, request, obj=None, **kwargs):
        self.parent_obj = obj
        formset = super().get_formset(request, obj, **kwargs)
        formset.obj = obj
        return formset

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'curriculum':
            kwargs['queryset'] = Curriculum.objects.filter(year=self.parent_obj.year)
        elif db_field.name == 'teacher':
            kwargs['queryset'] = Teacher.objects.filter(
                subjects__curriculums__in=Curriculum.objects.filter(year=self.parent_obj.year)
            ).distinct()
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def get_min_num(self, request, obj=None, **kwargs):
        return Curriculum.objects.filter(year=self.parent_obj.year).count()
