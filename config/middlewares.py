from django.contrib.auth.models import AnonymousUser
from users.models import User
from channels.middleware import BaseMiddleware
from channels.db import database_sync_to_async
from tokens.utils import check_token


@database_sync_to_async
def get_user(user_id):
    try:
        return User.objects.get(id=user_id)
    except User.DoesNotExist:
        return AnonymousUser()


class TokenAuthMiddleware(BaseMiddleware):
    async def __call__(self, scope, receive, send):
        """
        authentication through the access token in query_string for WebSocket
        """
        payload = check_token(scope['query_string'])

        if not payload:
            return

        scope['user'] = await get_user(int(payload['user_id']))

        return await super().__call__(scope, receive, send)
