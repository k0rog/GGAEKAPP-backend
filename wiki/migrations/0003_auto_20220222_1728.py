# Generated by Django 3.2.9 on 2022-02-22 17:28

from django.db import migrations, models
import django.db.models.deletion
import wiki.models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0003_auto_20220216_1834'),
        ('college', '0002_auto_20220214_1440'),
        ('wiki', '0002_article_subject'),
    ]

    operations = [
        migrations.AlterField(
            model_name='article',
            name='speciality',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='articles', to='college.speciality'),
        ),
        migrations.AlterField(
            model_name='article',
            name='subject',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='articles', to='college.subject'),
        ),
        migrations.AlterField(
            model_name='article',
            name='teacher',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='articles', to='users.teacher'),
        ),
        migrations.AlterField(
            model_name='articlefile',
            name='file',
            field=models.FileField(upload_to=wiki.models.get_file_path),
        ),
    ]
