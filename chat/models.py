import os
from django.core.files.images import ImageFile
from django.db import models
from users.models import User
from django.utils import timezone
from college.utils.picture_generator import generate_picture
from college.utils import aws_supplier, file_cleaner
from django.conf import settings


def get_cover_path(self, filename):
    return f'{self.title}/{filename}'


class Chat(models.Model):
    users = models.ManyToManyField(User, through='ChatUser', related_name='chats')
    cover = models.ImageField(upload_to=get_cover_path, null=True, default=None)
    title = models.CharField(max_length=255, unique=True)

    def __init__(self, *args, create_cover=True, **kwargs):
        super().__init__(*args, **kwargs)
        self.create_cover = create_cover

    def generate_picture(self):
        picture = generate_picture(self.title)
        media_url = settings.MEDIA_URL.lstrip("/")
        filename = f'{self.title}_default.jpeg'
        cover_path = get_cover_path(self, filename)

        aws_supplier.send_file(picture, f'{settings.MEDIA_URL.lstrip("/")}{cover_path}')

        if settings.REMOTE_FILE_STORAGE:
            aws_supplier.send_file(picture, f'{media_url}{cover_path}')
            self.cover = cover_path
        else:
            self.cover = ImageFile(picture, name=filename)

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        if not self.cover and self.create_cover:
            self.generate_picture()

        super().save(force_insert, force_update, using, update_fields)

    def update_members(self, valid_members):
        current_members = set(self.users.all())
        # if valid members are User child models set difference does not recognize them
        valid_members = [User.objects.get(pk=member.id) for member in valid_members]

        for invalid_member in set(current_members) - set(valid_members):
            ChatUser.objects.filter(chat=self, user=invalid_member).delete()

        for not_included_member in set(valid_members) - set(current_members):
            ChatUser.objects.create(chat=self, user=not_included_member)

    def delete(self, using=None, keep_parents=False):
        file_cleaner.delete_assigned_file(self.cover)
        for message in self.messages.all():
            message.delete()
        return super().delete(using, keep_parents)


class Message(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE, related_name='messages')
    text = models.TextField(blank=True)
    date = models.DateTimeField(default=timezone.now, db_index=True)
    articles = models.ManyToManyField('wiki.Article')

    def add_articles(self, article_ids):
        # circular import
        article_model = self.articles.model
        not_found_ids = []
        for article_id in article_ids:
            try:
                article = article_model.objects.get(pk=int(article_id))
            except article_model.DoesNotExist:
                not_found_ids.append(str(article_id))
                continue

            self.articles.add(article)

        return not_found_ids
    
    def update_articles(self, article_ids):
        # circular import
        article_model = self.articles.model
        current_articles = set([file['id'] for file in self.articles.all().values('id')])
        valid_articles = set([int(article_id) for article_id in article_ids])

        not_included_articles = []
        not_deleted_articles = []

        for invalid_article in current_articles - valid_articles:
            article = self.articles.filter(pk=invalid_article).first()
            if not article:
                not_deleted_articles.append(invalid_article)
                continue
            article.delete()

        for valid_article in valid_articles - current_articles:
            article = article_model.objects.filter(pk=valid_article).first()
            if not article:
                not_included_articles.append(valid_article)
                continue
            self.articles.add(article)

        errors = {}
        if len(not_included_articles):
            errors['not_included_articles'] = not_included_articles
        if len(not_deleted_articles):
            errors['not_deleted_articles'] = not_deleted_articles

        return errors if len(errors) else None
    
    def add_files(self, file_ids):
        not_found_ids = []
        for file_id in file_ids:
            try:
                file = File.objects.get(pk=int(file_id))
            except File.DoesNotExist:
                not_found_ids.append(str(file_id))
                continue

            self.files.add(file)

        return not_found_ids

    def update_files(self, file_ids):
        current_files = set([file['id'] for file in self.files.all().values('id')])
        valid_files = set([int(file_id) for file_id in file_ids])

        not_included_files = []
        not_deleted_files = []

        for invalid_file in current_files - valid_files:
            file = self.files.filter(pk=invalid_file).first()
            if not file:
                not_deleted_files.append(invalid_file)
                continue
            file.delete()

        for valid_file in valid_files - current_files:
            file = File.objects.filter(pk=valid_file).first()
            if not file:
                not_included_files.append(valid_file)
                continue
            self.files.add(file)

        errors = {}
        if len(not_included_files):
            errors['not_included_files'] = not_included_files
        if len(not_deleted_files):
            errors['not_deleted_files'] = not_deleted_files

        return errors if len(errors) else None

    def delete(self, using=None, keep_parents=False):
        for file in self.files.all():
            file.delete()
        super().delete(using, keep_parents)


class ChatUser(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE)
    last_read = models.IntegerField(null=True)

    def change_last_read(self, last_message_id):
        if not self.last_read:
            self.last_read = self.chat.messages.last().id
        elif last_message_id > self.last_read:
            self.last_read = last_message_id
        self.save()

        return self.last_read


def get_file_path(self, filename):
    return f'{self.chat.title}/{filename}'


class File(models.Model):
    IMAGE = 'IMG'
    DOCUMENT = 'DOC'

    FILE_TYPES = (
        (IMAGE, 'Image'),
        (DOCUMENT, 'Document'),
    )

    file_name = models.CharField(max_length=255, blank=True, default='')
    file_size = models.IntegerField(blank=True, default=0)
    file = models.FileField(upload_to=get_file_path, max_length=255)
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE, related_name='files')
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name='files', null=True)

    file_type = models.CharField(max_length=3, choices=FILE_TYPES, default=DOCUMENT)

    def save(self, *args, **kwargs):
        if 'image' in self.file.file.content_type:
            self.file_type = self.IMAGE

        self.file_name = '_'.join(os.path.basename(self.file.name).split())
        self.file_size = self.file.size
        super().save()

    def delete(self, using=None, keep_parents=False):
        file_cleaner.delete_assigned_file(self.file)
        return super().delete(using, keep_parents)
