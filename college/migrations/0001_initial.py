# Generated by Django 3.2.9 on 2022-02-10 19:59

import college.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('users', '__first__'),
    ]

    operations = [
        migrations.CreateModel(
            name='Curriculum',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ],
        ),
        migrations.CreateModel(
            name='Speciality',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255)),
                ('abbreviation', models.CharField(max_length=6)),
                ('group_prefix', models.CharField(max_length=3)),
            ],
        ),
        migrations.CreateModel(
            name='StudentGroup',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('number', models.IntegerField(verbose_name=college.validators.validate_group_number)),
                ('title', models.CharField(max_length=10, unique=True)),
                ('facilitator', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='assigned_group', to='users.teacher')),
            ],
        ),
        migrations.CreateModel(
            name='Subject',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255, unique=True)),
                ('abbreviation', models.CharField(max_length=10, unique=True)),
            ],
        ),
        migrations.CreateModel(
            name='Year',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('year', models.IntegerField(choices=[(1, 'First year'), (2, 'Second year'), (3, 'Third year'), (4, 'Fourth year')])),
                ('start_year', models.IntegerField(validators=[college.validators.validate_start_year])),
                ('speciality', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='years', to='college.speciality')),
                ('subjects', models.ManyToManyField(through='college.Curriculum', to='college.Subject')),
            ],
            options={
                'unique_together': {('speciality', 'year', 'start_year')},
            },
        ),
        migrations.CreateModel(
            name='StudentGroup_Curriculum',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('curriculum', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='college.curriculum')),
                ('student_group', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='college.studentgroup')),
                ('teacher', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='users.teacher')),
            ],
        ),
        migrations.AddField(
            model_name='studentgroup',
            name='subjects',
            field=models.ManyToManyField(related_name='student_groups', through='college.StudentGroup_Curriculum', to='college.Curriculum'),
        ),
        migrations.AddField(
            model_name='studentgroup',
            name='year',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='college.year'),
        ),
        migrations.AddField(
            model_name='curriculum',
            name='subject',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='college.subject'),
        ),
        migrations.AddField(
            model_name='curriculum',
            name='year',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='college.year'),
        ),
    ]
