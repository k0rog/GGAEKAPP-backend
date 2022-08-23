import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import Message, Chat
from .serializers import MessageSerializer
from tokens.utils import check_token


@database_sync_to_async
def check_chat_id(chat_id):
    return Chat.objects.filter(pk=chat_id).exists()


@database_sync_to_async
def is_chat_member(user, chat_id):
    chat = Chat.objects.get(pk=chat_id)
    return chat.users.filter(pk=user.id).exists()


@database_sync_to_async
def is_message_owner(user, message_id):
    return Message.objects.filter(pk=message_id, user=user.id).exists()


@database_sync_to_async
def serialize_message(message):
    serializer = MessageSerializer(instance=message)

    return dict(serializer.data)


@database_sync_to_async
def get_user_chats(user):
    return list(user.chats.all())


@database_sync_to_async
def save_new_message(data, scope):
    user = scope['user']

    chat = Chat.objects.get(pk=data['chat_id'])

    message = Message.objects.create(
        user=user,
        chat=chat,
        text=data['text']
    )

    errors = {}
    file_ids = message.add_files(data['files']) if 'files' in data else None
    if file_ids:
        errors['files'] = f'Files with the following ids not found: {", ".join(file_ids)}'
    article_ids = message.add_articles(data['articles']) if 'articles' in data else None
    if article_ids:
        errors['articles'] = f'Articles with the following ids not found: {", ".join(article_ids)}'

    if len(errors) == 0:
        errors = None

    return message, errors


@database_sync_to_async
def update_message(data):
    message = Message.objects.filter(pk=data['message_id']).first()
    if not message:
        return None, {'message': 'No message with this id found'}

    message.text = data['text']

    errors = {}
    file_errors = message.update_files(data['files']) if 'files' in data else None
    if file_errors:
        errors['files'] = file_errors
    article_errors = message.update_articles(data['articles']) if 'articles' in data else None
    if article_errors:
        errors['articles'] = article_errors

    if len(errors) == 0:
        errors = None

    message.save()

    return message, errors


@database_sync_to_async
def delete_message(data):
    message = Message.objects.filter(pk=data['message_id']).first()
    if not message:
        return {'message': 'No message with this id found'}

    message.delete()


class ChatConsumer(AsyncWebsocketConsumer):
    ALLOWED_MESSAGE_TYPES = ['new_message', 'update_message', 'delete_message']

    async def connect(self):
        user_chats = await get_user_chats(self.scope['user'])
        for chat in user_chats:
            await self.channel_layer.group_add(
                str(chat.id),
                self.channel_name,
            )

        await self.accept()

    async def disconnect(self, close_code):

        user_chats = await get_user_chats(self.scope['user'])

        for chat in user_chats:
            await self.channel_layer.group_discard(
                str(chat.id),
                self.channel_name,
            )

    async def success_message(self, event):
        response = {
            'status': 'success',
            'message': event['message']
        }

        await self.send(text_data=json.dumps(response))

    async def send_error_message(self, message):
        response = {
            'status': 'error',
            'message': message
        }

        await self.send(text_data=json.dumps(response))

    async def websocket_receive(self, message):
        # invalid token
        payload = check_token(self.scope['query_string'])
        if not payload:
            await self.close()
            return

        if 'text' not in message:
            await self.send_error_message({'message': 'No message sent'})
            return

        await self.receive(text_data=message['text'])

    async def validate_payload(self, payload):
        if not payload['chat_id']:
            return {'chat': 'No chat_id specified'}

        if not await is_chat_member(self.scope['user'], payload['chat_id']):
            return {'chat_id': 'You are not member of this chat'}

        if 'message_type' not in payload:
            return {'message_type': 'message_type not specified'}

        if payload['message_type'] not in self.ALLOWED_MESSAGE_TYPES:
            return {'message_type': f'Wrong message type. '
                                    f'Allowed types: {", ".join(self.ALLOWED_MESSAGE_TYPES)}'}

        if not await check_chat_id(payload['chat_id']):
            return {'chat_id': f'Chat with id {payload["chat_id"]} not found'}

    async def validate_message_id(self, data):
        if 'message_id' not in data or not isinstance(data['message_id'], int):
            return {'message_id': 'No message id specified or specified wrong type'}

        if not await is_message_owner(self.scope['user'], data['message_id']):
            return {'message_id': 'You are trying to modify not your message'}

    # Receive message from WebSocket
    async def receive(self, text_data=None, bytes_data=None):
        data = json.loads(text_data)

        if 'message' not in data:
            await self.send_error_message({'message': 'No message sent'})
            return

        payload = data['message']

        errors = await self.validate_payload(payload)

        if errors:
            await self.send_error_message(errors)
            return

        if payload['message_type'] == 'new_message':
            await self.new_message(payload)
        elif payload['message_type'] == 'update_message':
            await self.update_message(payload)
        elif payload['message_type'] == 'delete_message':
            await self.delete_message(payload)

    async def new_message(self, payload):
        message, errors = await save_new_message(payload, self.scope)

        response = await serialize_message(message)

        if errors:
            response['errors'] = errors

        if 'client_side_id' in payload:
            response['client_side_id'] = payload['client_side_id']

        response['message_type'] = payload['message_type']

        await self.channel_layer.group_send(
            str(payload['chat_id']),
            {
                'type': 'success_message',
                'message': response
            }
        )

    async def update_message(self, payload):
        errors = await self.validate_message_id(payload)
        if errors:
            await self.send_error_message(errors)
            return

        message, errors = await update_message(payload)
        if not message:
            await self.send_error_message(errors)
            return

        response = await serialize_message(message)

        if errors:
            response['errors'] = errors

        response['message_type'] = payload['message_type']

        await self.channel_layer.group_send(
            str(payload['chat_id']),
            {
                'type': 'success_message',
                'message': response
            }
        )

    async def delete_message(self, payload):
        errors = await self.validate_message_id(payload)
        if errors:
            await self.send_error_message(errors)
            return

        errors = await delete_message(payload)

        if errors:
            await self.send_error_message(errors)
            return

        response = {'message_id': payload['message_id'], 'chat_id': payload['chat_id'],
                    'message_type': payload['message_type']}

        await self.channel_layer.group_send(
            str(payload['chat_id']),
            {
                'type': 'success_message',
                'message': response
            }
        )
