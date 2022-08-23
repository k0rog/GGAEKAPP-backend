from collections import OrderedDict
from rest_framework import viewsets, generics
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.pagination import CursorPagination
from .serializers import FileSerializer, MessageSerializer
from .models import Message, ChatUser, File, Chat
from .permissions import IsChatMember
from rest_framework import status
from rest_framework.generics import ListAPIView
from users.serializers import ChatUserSerializer


class ChatUsersView(ListAPIView):
    serializer_class = ChatUserSerializer

    def get_queryset(self):
        return Chat.objects.filter(pk=self.kwargs['chat_id']).first().users.all()


def get_cursor_from_url(url):
    get_params = url.split('?')[1].split('&')
    for param in get_params:
        key, value = param.split('=')
        if key == 'cursor':
            return value


class CustomCursorPaginator(CursorPagination):
    def get_paginated_response(self, data):
        next_link = self.get_next_link()
        next_cursor = get_cursor_from_url(next_link) if next_link else None

        previous_link = self.get_previous_link()
        previous_cursor = get_cursor_from_url(previous_link) if previous_link else None

        return Response(OrderedDict([
            ('next', next_cursor),
            ('previous', previous_cursor),
            ('results', data),
        ]))


class CursorFilePagination(CustomCursorPaginator):
    page_size = 36
    ordering = '-id'


class ChatFilesViewSet(viewsets.ModelViewSet):
    permission_classes = [IsChatMember]
    parser_classes = (FormParser, MultiPartParser)
    lookup_url_kwarg = 'chat_id'
    pagination_class = CursorFilePagination
    serializer_class = FileSerializer

    def get_queryset(self):
        file_type = self.request.GET.get('file_type', None)

        if not file_type:
            return []

        return File.objects.filter(chat_id=self.kwargs['chat_id'], file_type=file_type)

    def list(self, request, *args, **kwargs):
        file_type = self.request.GET.get('file_type', None)

        if not file_type:
            return Response(data={'message': 'Specify the query parameter file_type. '
                                             'IMG and DOC are available'},
                            status=status.HTTP_400_BAD_REQUEST)

        return super().list(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        request.data['chat'] = kwargs['chat_id']
        serializer = FileSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CursorMessagePagination(CustomCursorPaginator):
    page_size = 15
    ordering = '-date'


class ChatMessagesView(generics.ListAPIView):
    pagination_class = CursorMessagePagination
    serializer_class = MessageSerializer
    permission_classes = [IsChatMember]
    lookup_url_kwarg = 'chat_id'

    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def get_queryset(self):
        return Message.objects.select_related('user', 'chat') \
            .prefetch_related('files').filter(chat_id=self.kwargs['chat_id'])

    def get_paginated_response(self, data):
        chat_user = ChatUser.objects.select_related('chat').get(user=self.request.user,
                                                                chat_id=self.kwargs['chat_id'])

        response = self.paginator.get_paginated_response(data)

        if not response.data['results']:
            return response

        last_message_id = response.data['results'][0]['id']

        response.data['last_read'] = chat_user.change_last_read(last_message_id)

        return response
