from college.models import YEARS, Speciality, Subject
from college.utils import file_cleaner
from users.models import Teacher
from django.db import models


class Article(models.Model):
    title = models.CharField(max_length=255)
    text = models.TextField()
    speciality = models.ForeignKey(Speciality, on_delete=models.CASCADE, related_name='articles')
    year = models.IntegerField(choices=YEARS)
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name='articles')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='articles')

    def update_files(self, file_ids):
        current_files = set([file['id'] for file in self.files.all().values('id')])
        valid_files = set([int(file_id) for file_id in file_ids])

        errors = {
            'not_included_files': [],
            'not_deleted_files': []
        }

        for invalid_file in current_files - valid_files:
            file = self.files.filter(pk=invalid_file).first()
            if not file:
                errors['not_deleted_files'].append(invalid_file)
                continue
            file.delete()

        for valid_file in valid_files - current_files:
            file = ArticleFile.objects.filter(pk=valid_file).first()
            if not file:
                errors['not_included_files'].append(valid_file)
                continue
            self.files.add(file)

        return errors

    def delete(self, using=None, keep_parents=False):
        for file in self.files.all():
            file.delete()
        return super().delete(using, keep_parents)


def get_file_path(self, filename):
    return f'{self.article.speciality.abbreviation}/{self.article.year}/' \
           f'{self.article.teacher}/{self.article.title}/{filename}'


class ArticleFile(models.Model):
    file = models.FileField(upload_to=get_file_path, max_length=255)
    article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name='files')

    def delete(self, using=None, keep_parents=False):
        file_cleaner.delete_assigned_file(self.file)
        return super().delete(using, keep_parents)
