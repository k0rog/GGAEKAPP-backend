import json
from urllib import parse
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from .utils.user_creator import USER_DATA
from .mixins import TestUserAuthenticationMixin, TestSecondUserAuthenticationMixin
from chat.models import Chat, ChatUser, Message
import io
from django.conf import settings


class AuthenticationFailedTestCase(APITestCase):
    url_name = 'me'
    url = reverse(url_name)

    def test_me(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(json.loads(response.content),
                         {'detail': 'Authentication credentials were not provided.'})


class IDSpecifiedUserTestCase(TestUserAuthenticationMixin, APITestCase):
    def test_retrieve(self):
        response = self.client.get(reverse('exact_user', kwargs={'user_id': 1}))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(json.loads(response.content),
                         {
                             'id': 1,
                             'first_name': USER_DATA['first_name'],
                             'last_name': USER_DATA['last_name'],
                             'email': USER_DATA['email'],
                             'avatar': None
                         })

    def create_chats(self):
        Chat.objects.bulk_create([
            Chat(title='something1'),
            Chat(title='something2'),
        ])

        ChatUser.objects.bulk_create([
            ChatUser(user=self.user, chat=chat) for chat in Chat.objects.all()])

    def test_get_chat_list(self):
        self.create_chats()

        response = self.client.get(reverse('user_chats', kwargs={'user_id': 1}))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(json.loads(response.content), [
            {'id': 1, 'title': 'something1', 'cover': None, 'last_message': None},
            {'id': 2, 'title': 'something2', 'cover': None, 'last_message': None}])

    def test_get_chat_list_with_last_message(self):
        self.create_chats()
        Message.objects.bulk_create(
            [Message(user=self.user, chat=chat, text='something') for chat in Chat.objects.all()]
        )

        response = self.client.get(reverse('user_chats', kwargs={'user_id': 1}))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(json.loads(response.content), [
            {'id': message.chat.id, 'title': message.chat.title, 'cover': None,
             'last_message':
                 {'id': message.id, 'text': 'something',
                  'date': f'{message.date.isoformat().split("+")[0]}Z',
                  'user': {'avatar': None}}
             } for message in Message.objects.all()])


class IDSpecifiedOtherUserTestCase(TestSecondUserAuthenticationMixin, APITestCase):
    def test_retrieve(self):
        response = self.client.get(reverse('exact_user', kwargs={'user_id': 1}))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(json.loads(response.content),
                         {
                             'id': 1,
                             'first_name': USER_DATA['first_name'],
                             'last_name': USER_DATA['last_name'],
                             'avatar': None
                         })


class MeActionsTestCase(TestUserAuthenticationMixin, APITestCase):
    test_file_path = settings.STATIC_ROOT + 'testpic/2Rt1hFEiPzQ.jpg'
    filename = test_file_path.split("/")[-1]

    def test_me_retrieve(self):
        response = self.client.get(reverse('me'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(json.loads(response.content),
                         {
                             'id': 1,
                             'first_name': USER_DATA['first_name'],
                             'last_name': USER_DATA['last_name'],
                             'email': USER_DATA['email'],
                             'avatar': None
                         })

    def test_me_change_email(self):
        response = self.client.patch(reverse('self_email'),
                                     {'email': 'test@mail.ru', 'password': USER_DATA['password']},
                                     format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(json.loads(response.content), {'email': 'test@mail.ru'})

    def test_me_change_password(self):
        response = self.client.patch(reverse('self_password'),
                                     {'old_password': USER_DATA['password'],
                                      'new_password': 'something'},
                                     format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(json.loads(response.content), {'message': 'Password has benn changed successfully.'})

    def test_avatar_change(self):
        with open(self.test_file_path) as file:
            picture = io.FileIO(file.fileno())
            picture.name = self.filename

            response = self.client.post(reverse('self_avatar'), data={'avatar': picture})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(json.loads(response.content),
                         {'avatar': parse.quote(
                             f'{settings.MEDIA_URL}{USER_DATA["email"]}/{self.filename}')})
