from django import forms
from django.contrib.admin.widgets import FilteredSelectMultiple
from users.models import Teacher
from .models import Subject
from django.utils.translation import gettext_lazy as _


class SubjectAdminForm(forms.ModelForm):
    teachers = forms.ModelMultipleChoiceField(
        queryset=Teacher.objects.all(),
        label=_('Teachers'),
        required=False,
        widget=FilteredSelectMultiple(
            verbose_name=_('Teachers'),
            is_stacked=False
        )
    )

    class Meta:
        model = Subject
        fields = ['title', 'abbreviation', 'teachers']


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.instance and self.instance.pk:
            self.fields['teachers'].initial = self.instance.teachers.all()

    def save(self, commit=True):
        user = super().save(commit=False)

        if commit:
            user.save()

        if user.pk:
            user.teachers = self.cleaned_data['teachers']
            self.save_m2m()

        return user
