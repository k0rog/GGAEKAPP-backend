from django.conf import settings
from django.test import TestCase
from users.models import User
from .utils.user_creator import USER_DATA
import urllib.parse


class UserSerializerPictureCreationTestCase(TestCase):
    def test_avatar_creation(self):
        user = User(**USER_DATA, create_avatar=True)
        user.save()
        user.set_password(USER_DATA['password'])
        user.save()

        self.assertEqual(user.email, USER_DATA['email'])
        self.assertEqual(user.first_name, USER_DATA['first_name'])
        self.assertEqual(user.last_name, USER_DATA['last_name'])
        self.assertTrue(user.check_password(USER_DATA['password']))

        initials = f'{USER_DATA["first_name"][0].upper()}{USER_DATA["last_name"][0].upper()}'
        self.assertEqual(urllib.parse.unquote(user.avatar.url),
                         f'{settings.MEDIA_URL}{USER_DATA["email"]}/{initials}.jpeg')
