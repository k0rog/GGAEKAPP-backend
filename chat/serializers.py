from rest_framework import serializers
from .models import Chat, Message, File
from users.models import User
from wiki.models import Article


class FileSerializer(serializers.ModelSerializer):
    class Meta:
        model = File
        fields = ['id', 'file', 'file_name', 'file_size', 'file_type', 'chat']
        extra_kwargs = {
            'chat': {
                'write_only': True
            }
        }


class ArticleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Article
        fields = ['id', 'title']


class UserMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'first_name', 'last_name', 'avatar']


class MessageSerializer(serializers.ModelSerializer):
    files = FileSerializer(many=True, read_only=True)
    articles = ArticleSerializer(many=True, read_only=True)

    def to_representation(self, instance):
        representation = super().to_representation(instance)

        representation['user'] = UserMessageSerializer(instance=instance.user).data

        return representation

    class Meta:
        model = Message
        fields = ['id', 'chat_id', 'files', 'articles', 'text', 'date']


class ChatSerializer(serializers.ModelSerializer):
    def to_representation(self, instance):
        representation = super().to_representation(instance)

        last_message = instance.messages.select_related('user').last()
        if last_message:
            representation['last_message'] = {
                'id': last_message.id,
                'text': last_message.text,
                'date': last_message.date,
                'user': {
                    'avatar': last_message.user.avatar.url if last_message.user.avatar else None
                }
            }
        else:
            representation['last_message'] = None

        return representation

    class Meta:
        model = Chat
        fields = ['id', 'title', 'cover']
