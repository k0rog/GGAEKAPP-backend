import json
import os
from urllib import parse
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from users.tests.mixins import TestUserAuthenticationMixin
from chat.models import Chat, ChatUser, Message
import io
from django.conf import settings
from shutil import rmtree
from .utils.string_generator import generate_string
from chat.serializers import MessageSerializer
import mimetypes


class ChatFilesTestCase(TestUserAuthenticationMixin, APITestCase):
    test_file_folder = 'testfiles'
    test_file_folder_path = os.path.join(settings.STATIC_ROOT, test_file_folder)

    test_chat_title = 'TestChat'

    maxDiff = None

    def setUp(self):
        super().setUp()

        self.chat = Chat.objects.create(title=self.test_chat_title)
        ChatUser.objects.create(chat=self.chat, user=self.user)

    def tearDown(self):
        rmtree(os.path.join(settings.MEDIA_ROOT, self.test_chat_title))

    def send_file(self, filename):
        file_path = os.path.join(settings.STATIC_ROOT, self.test_file_folder, filename)

        with open(file_path) as file:
            send_file = io.FileIO(file.fileno())
            send_file.name = filename

            response = self.client.post(reverse('chat_files/', kwargs={'chat_id': 1}), data={'file': send_file})

        return response

    def serialize_file(self, filename, pk):
        file_path = os.path.join(settings.STATIC_ROOT, self.test_file_folder, filename)
        file_size = os.stat(file_path).st_size

        file_type = 'IMG' if 'image' in mimetypes.guess_type(file_path)[0] else 'DOC'

        filename = '_'.join(filename.split(' '))

        file_data = {
            'id': pk,
            'file': parse.quote(os.path.join(settings.MEDIA_URL, self.test_chat_title, filename)),
            'file_name': filename,
            'file_size': file_size,
            'file_type': file_type
        }

        return file_data

    def assert_test_file(self, filename, pk=1):
        response = self.send_file(filename)

        file_data = self.serialize_file(filename, pk)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertEqual(json.loads(response.content), file_data)

        return file_data

    def test_file_send(self):
        filename = os.listdir(self.test_file_folder_path)[0]

        self.assert_test_file(filename)

    def test_list_files(self):
        files = []
        for i, filename in enumerate(os.listdir(self.test_file_folder_path)):
            files.append(self.assert_test_file(filename, i + 1))

        response = self.client.get(reverse('chat_files', kwargs={'chat_id': 1}))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', json.loads(response.content))

        content = json.loads(response.content)

        while True:
            for file in content['results']:
                self.assertEqual(file, files.pop())

            if not content['next']:
                break

            content = json.loads(self.client.get(content['next']).content)


class ChatMessagesTestCase(TestUserAuthenticationMixin, APITestCase):
    test_chat_title = 'TestChat'

    def setUp(self):
        super().setUp()

        self.chat = Chat.objects.create(title=self.test_chat_title)
        ChatUser.objects.create(chat=self.chat, user=self.user)

        self.messages = []

        for i in range(10):
            self.messages.append(Message.objects.create(text=generate_string(), user=self.user, chat=self.chat))

    def tearDown(self):
        rmtree(os.path.join(settings.MEDIA_ROOT, self.test_chat_title))

    def test_list_messages(self):
        response = self.client.get(reverse('chat_messages', kwargs={'chat_id': 1}))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', json.loads(response.content))

        content = json.loads(response.content)

        while True:
            for chat_message in content['results']:
                self.assertEqual(chat_message, MessageSerializer(instance=self.messages.pop()).data)

            if not content['next']:
                break

            content = json.loads(self.client.get(content['next']).content)
