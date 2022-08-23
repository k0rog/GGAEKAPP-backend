from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from .models import Article, ArticleFile
from college.models import Speciality, Year


class YearSerializer(serializers.ModelSerializer):
    class Meta:
        model = Year
        fields = ['year']


class SpecialitySerializer(serializers.ModelSerializer):
    years = YearSerializer(many=True)

    class Meta:
        model = Speciality
        fields = ['id', 'abbreviation', 'years']


class ArticleFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = ArticleFile
        fields = ['id', 'file', 'article']
        extra_kwargs = {
            'article': {
                'write_only': True
            }
        }

    def validate_article(self, value):
        if not self.context['teacher'].articles.filter(pk=value.id).exists():
            raise ValidationError(_('This teacher has no right to add files to this article'))
        return value


class ArticleSerializer(serializers.ModelSerializer):
    files = ArticleFileSerializer(many=True, read_only=True)

    class Meta:
        model = Article
        fields = ['id', 'title', 'text', 'speciality', 'year', 'teacher', 'subject', 'files']

    def validate_subject(self, value):
        if not self.context['teacher'].subjects.filter(pk=value.id):
            raise ValidationError(_('This teacher has no right to teach this subject'))
        return value
