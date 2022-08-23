from django.contrib import admin
from users.models import Staff, Teacher
from .models import StudentGroup
from .models import Subject, Speciality, Year, Curriculum
from .forms import SubjectAdminForm
from .inlines import SubjectInline, StudentInline
from .mixins import AdminReallyDeleteActionMixin


@admin.register(Speciality)
class SpecialityAdmin(admin.ModelAdmin):
    fields = ['title', 'abbreviation', 'group_prefix']
    list_display = ['abbreviation']


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    form = SubjectAdminForm


class CurriculumInline(admin.TabularInline):
    model = Curriculum
    extra = 1
    fields = ['subject']


@admin.register(Year)
class YearAdmin(admin.ModelAdmin):
    fields = ['speciality', 'year', 'start_year']
    inlines = [CurriculumInline]
    list_display = ['speciality', 'year', 'start_year']


# Users classes start
@admin.register(Staff)
class StaffAdmin(admin.ModelAdmin):
    fields = ['first_name', 'last_name', 'email', 'groups']
    list_display = ['first_name', 'last_name', 'email']
    list_display_links = ['email']

    def get_queryset(self, request):
        allowed_groups = request.user.get_allowed_groups()
        return Staff.objects.filter(groups__in=allowed_groups)

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        # when creating new user, admin have only allowed permission groups to assign
        if db_field.name == "groups":
            kwargs["queryset"] = request.user.get_allowed_groups()

        return super().formfield_for_manytomany(db_field, request, **kwargs)


@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    fields = ['first_name', 'last_name', 'email', 'subjects']
    list_display = ['first_name', 'last_name', 'email']
    list_display_links = ['email']
    filter_horizontal = ['subjects']
# Users classes end


@admin.register(StudentGroup)
class StudentGroupAdmin(AdminReallyDeleteActionMixin, admin.ModelAdmin):
    fields = ['number', 'facilitator', 'year']
    list_display = ['title', 'facilitator']

    def get_inlines(self, request, obj):
        if obj:
            return [SubjectInline, StudentInline]
        return [StudentInline]

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ['number']
        return []

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        student_group = form.instance
        student_group.update_group_chat()
        student_group.update_subject_chats()
