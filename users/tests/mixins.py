import os
import shutil
from users.tests.utils.user_creator import create_user, SECOND_USER_DATA, USER_DATA
from rest_framework_simplejwt.tokens import RefreshToken
from django.conf import settings


class TestUserAuthenticationMixin:
    def setUp(self):
        settings.DEBUG = True
        self.user = create_user()
        self.token = RefreshToken.for_user(self.user).access_token
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + str(self.token))

    def tearDown(self):
        shutil.rmtree(os.path.join(settings.MEDIA_ROOT, USER_DATA['email']))


class TestSecondUserAuthenticationMixin:
    def setUp(self):
        create_user()
        self.user = create_user(SECOND_USER_DATA)
        self.token = RefreshToken.for_user(self.user).access_token
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + str(self.token))

    def tearDown(self):
        shutil.rmtree(os.path.join(settings.MEDIA_ROOT, SECOND_USER_DATA['email']))
