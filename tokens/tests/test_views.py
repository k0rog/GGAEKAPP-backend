import json
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.core.management import call_command
from users.tests.utils.user_creator import create_user, USER_DATA
from jwt import decode
from jwt.exceptions import InvalidTokenError
from django.conf import settings


class TokensTestCase(APITestCase):
    def setUp(self) -> None:
        create_user()

    def check_token(self, token):
        try:
            token_data = decode(token, settings.SECRET_KEY, algorithms=['HS256'])
            self.assertEqual(token_data['user_id'], 1)
        except InvalidTokenError:
            self.assertEqual(1, 0)

    def test_login(self):
        response = self.client.post(reverse('login'),
                                    {'email': USER_DATA['email'], 'password': USER_DATA['password']},
                                    format='json')

        access_token = response.cookies.get('access').value
        refresh_token = response.cookies.get('refresh').value

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.cookies)
        self.assertIn('refresh', response.cookies)

        self.assertEqual(json.loads(response.content),
                         {'access': access_token})

        self.check_token(access_token)
        self.check_token(refresh_token)

    def test_refresh_token(self):
        login_response = self.client.post(reverse('login'),
                                          {'email': USER_DATA['email'], 'password': USER_DATA['password']},
                                          format='json')

        refresh_token = login_response.cookies.get('refresh')
        self.client.cookies['refresh'] = refresh_token
        response = self.client.post(reverse('refresh'))

        access_token = response.cookies.get('access').value

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.cookies)
        self.assertEqual(json.loads(response.content),
                         {'access': access_token})
        self.check_token(access_token)