from django.urls import path
from . import views

urlpatterns = [
    path('<int:chat_id>/files', views.ChatFilesViewSet.as_view({'get': 'list'}), name='chat_files'),
    path('<int:chat_id>/files/', views.ChatFilesViewSet.as_view({'post': 'create'}), name='chat_files/'),

    path('<int:chat_id>/users', views.ChatUsersView.as_view(), name='chat_users'),

    path('<int:chat_id>/messages/', views.ChatMessagesView.as_view(), name='chat_messages')
]
