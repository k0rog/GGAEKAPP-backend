# Generated by Django 3.2.9 on 2022-03-21 16:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0006_rename_first_login_user_temporary_password'),
    ]

    operations = [
        migrations.AddField(
            model_name='emailverification',
            name='done',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='emailverification',
            name='new_value',
            field=models.CharField(max_length=255, null=True),
        ),
    ]
