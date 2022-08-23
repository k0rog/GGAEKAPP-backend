from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from .models import User, Student, Teacher


class UserSerializer(serializers.ModelSerializer):
    def to_representation(self, instance):
        representation = super().to_representation(instance)

        user_group = instance.groups.first()
        if user_group:
            representation['group_name'] = user_group.name

        print(user_group.name)
        if user_group.name == 'student':
            student = Student.objects.filter(pk=instance.id).first()
            representation['year'] = student.group.year.year
            representation['speciality'] = {
                'id': student.group.year.speciality.id,
                'title': student.group.year.speciality.abbreviation
            }
            representation['abbreviation'] = student.group.year.speciality.abbreviation
        elif user_group.name == 'teacher':
            subject_ids = [subject['id'] for subject in
                           Teacher.objects.get(pk=instance.id).subjects.all().values('id')]
            representation['subjects'] = subject_ids

        if self.context['request'].user.id == instance.id or \
                self.context['request'].user.groups.first().name != 'student' or instance.phone_publicity:
            representation['phone_number'] = instance.phone_number

        if self.context['request'].user.id == instance.id:
            representation['email'] = instance.email

        if self.context['request'].user.temporary_password:
            representation['temporary_password'] = True

        return representation

    class Meta:
        model = User
        fields = ['id', 'first_name', 'last_name', 'avatar', 'phone_number', 'phone_publicity']
        extra_kwargs = {
            'phone_number': {
                'write_only': True
            },
            'avatar': {
                'read_only': True
            }
        }


class ChatUserSerializer(serializers.ModelSerializer):
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        if self.context['request'].user.id == instance.id or \
                self.context['request'].user.groups.first().name != 'student' or instance.phone_publicity:
            representation['phone_number'] = instance.phone_number
        return representation

    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'avatar']


class UserChangeAvatarSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['avatar']
        extra_kwargs = {
            'avatar': {
                'required': True
            }
        }

    def save(self, *args, **kwargs):
        if self.instance.avatar:
            self.instance.avatar.delete()
        return super().save(**kwargs)


class UserChangeEmailSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['password', 'email']
        extra_kwargs = {
            'password': {
                'write_only': True
            }
        }

    def validate_password(self, value):
        if not self.instance.check_password(value):
            raise ValidationError('Wrong password')
        return value

    def update(self, instance, validated_data):
        email = validated_data.get('email', None)
        instance.email = email
        instance.set_password(email)
        instance.save()
        return instance


class TestUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'first_name', 'last_name', 'email', 'password']
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        instance = self.Meta.model(**validated_data)
        instance.save()

        if password is not None:
            instance.set_password(password)
            instance.save()

        return instance
