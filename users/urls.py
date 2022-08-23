from django.urls import path
from .import views

urlpatterns = [
    path('<int:user_id>', views.UserRetrieveView.as_view(), name='exact_user'),
    path('<int:user_id>/chats', views.UserChatsView.as_view(), name='user_chats'),
    path('me', views.UserSelfView.as_view({'get': 'retrieve'}), name='me'),
    path('me/', views.UserSelfView.as_view({'patch': 'update'}), name='me/'),
    path('me/avatar/', views.UserChangeAvatarView.as_view(), name='self_avatar'),
    path('me/password/', views.UserChangePasswordView.as_view(), name='self_password'),
    path('password/', views.UserForgotPasswordView.as_view(), name='forgot_password'),
    path('password/verification/', views.UserForgotPasswordVerificationView.as_view(),
         name='forgot_password_verification'),
    path('password/verification/completion/', views.UserForgotPasswordNewPassword.as_view(),
         name='forgot_password_completion'),
    path('me/email/', views.UserChangeEmailView.as_view(), name='self_email'),
    path('me/email/verification/', views.UserChangeEmailVerificationView.as_view(), name='self_email_verification'),
]
