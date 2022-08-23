from django.contrib import admin
from .models import Article, ArticleFile
from users.models import Teacher
from college.models import Speciality
from college.mixins import AdminReallyDeleteActionMixin


class FileInline(admin.TabularInline):
    model = ArticleFile
    fields = ['file']
    extra = 1


@admin.register(Article)
class ArticleAdmin(AdminReallyDeleteActionMixin, admin.ModelAdmin):
    fields = ['title', 'text', 'speciality', 'year', 'subject']
    list_display = ['title', 'speciality', 'year', 'subject']
    inlines = [FileInline]

    def get_form(self, request, obj=None, change=False, **kwargs):
        self.teacher = Teacher.objects.get(pk=request.user.id)
        return super().get_form(request, obj, change, **kwargs)

    def get_queryset(self, request):
        return Article.objects.filter(teacher=request.user)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'subject':
            kwargs['queryset'] = self.teacher.subjects.all()
        elif db_field.name == 'speciality':
            kwargs['queryset'] = Speciality.objects.filter(years__subjects__teachers__exact=self.teacher).distinct()
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def save_model(self, request, obj, form, change):
        obj.teacher = self.teacher
        super().save_model(request, obj, form, change)
