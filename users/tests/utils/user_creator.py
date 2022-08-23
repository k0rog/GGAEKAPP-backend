from users.serializers import TestUserSerializer


USER_DATA = {
    'first_name': 'Ilya',
    'last_name': 'Auramenka',
    'email': 'a@a.com',
    'password': 'a'
}

SECOND_USER_DATA = {
    'first_name': 'Ilya',
    'last_name': 'Auramenka',
    'email': 'b@a.com',
    'password': 'a'
}


def create_user(data=None):
    if data is None:
        data = USER_DATA

    serializer = TestUserSerializer(data=data)

    if serializer.is_valid():
        return serializer.save()
