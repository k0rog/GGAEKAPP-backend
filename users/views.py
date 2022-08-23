from hashlib import sha256

from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.generics import RetrieveAPIView, UpdateAPIView, ListAPIView
from rest_framework import viewsets, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import User, EmailVerification
from chat.serializers import ChatSerializer
from chat.models import Chat
from . import serializers
from .permissions import IsOwner
from django.utils.crypto import get_random_string
from django.core.mail import send_mail
from django.utils.translation import gettext_lazy as _
from django.core.validators import validate_email
from django.core.exceptions import ValidationError


class UserRetrieveView(RetrieveAPIView):
    queryset = User.objects.all()
    lookup_url_kwarg = 'user_id'
    serializer_class = serializers.UserSerializer


class UserChatsView(ListAPIView):
    permission_classes = [IsOwner]
    serializer_class = ChatSerializer

    def get_queryset(self):
        return Chat.objects.filter(chatuser__user=self.request.user)


class UserSelfView(viewsets.ModelViewSet):
    serializer_class = serializers.UserSerializer
    queryset = User.objects.all()

    def get_object(self):
        return self.request.user

    def update(self, request, *args, **kwargs):
        serializer = serializers.UserSerializer(instance=request.user, data=request.data,
                                                partial=True, context={'request': self.request})

        if serializer.is_valid():
            serializer.save()
            return Response(data=serializer.data, status=status.HTTP_200_OK)
        return Response(data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserChangeAvatarView(APIView):
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        serializer = serializers.UserChangeAvatarSerializer(data=request.data, instance=request.user)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserChangePasswordView(UpdateAPIView):
    def update(self, request, *args, **kwargs):
        if 'old_password' not in request.data or 'new_password' not in request.data:
            return Response({'message': 'specify the old_password and new_password fields'})

        user = request.user

        if not user.check_password(request.data.get('old_password')):
            return Response({'old_password': ['Wrong password.']}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(request.data.get('new_password'))

        if user.temporary_password:
            user.temporary_password = False

        user.save()

        return Response(data={'message': 'Password has benn changed successfully.'}, status=status.HTTP_200_OK)


class UserForgotPasswordView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        if 'email' not in request.data:
            return Response(data={'email': 'Field is not specified'}, status=status.HTTP_409_CONFLICT)

        try:
            validate_email(request.data['email'])
        except ValidationError:
            return Response(data={'email': 'Value does not matches email address pattern'},
                            status=status.HTTP_409_CONFLICT)

        user = User.objects.filter(email=request.data['email']).first()

        if not user:
            return Response(data={'email': 'User with this email is already exists'},
                            status=status.HTTP_409_CONFLICT)

        verification_code = get_random_string(length=8, allowed_chars='0123456789')

        send_mail(
            _('Verification password code'),
            verification_code,
            from_email=None,
            recipient_list=[request.data['email']],
            fail_silently=False
        )

        try:
            verification = EmailVerification.objects.get(user=user,
                                                         verification_type=EmailVerification.PASSWORD)
            verification.code = verification_code
            verification.save()
        except EmailVerification.DoesNotExist:
            EmailVerification.objects.create(user=user,
                                             verification_type=EmailVerification.PASSWORD,
                                             code=verification_code)

        return Response(data={'message': 'code_sent'}, status=status.HTTP_200_OK)


class UserForgotPasswordVerificationView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        if 'code' not in request.data:
            return Response(data={'code': 'Field is not specified'}, status=status.HTTP_409_CONFLICT)

        if 'email' not in request.data:
            return Response(data={'email': 'Field is not specified'}, status=status.HTTP_409_CONFLICT)

        try:
            validate_email(request.data['email'])
        except ValidationError:
            return Response(data={'email': 'Value does not matches email address pattern'},
                            status=status.HTTP_409_CONFLICT)

        user = User.objects.filter(email=request.data['email']).first()

        if not user:
            return Response(data={'email': 'Email not found'},
                            status=status.HTTP_409_CONFLICT)

        verification = EmailVerification.objects.filter(user=user,
                                                        verification_type=EmailVerification.PASSWORD).first()

        if not verification:
            return Response(data={'verification': 'Forgot password request had not been sent. Send it please'},
                            status=status.HTTP_409_CONFLICT)

        if int(request.data['code']) != verification.code:
            return Response(data={'code': 'Wrong code'},
                            status=status.HTTP_409_CONFLICT)

        verification.done = True
        verification.save()

        return Response(data={'message': 'Verification done'}, status=status.HTTP_200_OK)


class UserForgotPasswordNewPassword(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        if 'new_password' not in request.data:
            return Response(data={'password': 'Password is not specified'}, status=status.HTTP_409_CONFLICT)

        if 'email' not in request.data:
            return Response(data={'email': 'Field is not specified'}, status=status.HTTP_409_CONFLICT)

        try:
            validate_email(request.data['email'])
        except ValidationError:
            return Response(data={'email': 'Value does not matches email address pattern'},
                            status=status.HTTP_409_CONFLICT)

        user = User.objects.filter(email=request.data['email']).first()

        if not user:
            return Response(data={'email': 'Email not found'},
                            status=status.HTTP_409_CONFLICT)

        verification = EmailVerification.objects.filter(user=user,
                                                        verification_type=EmailVerification.PASSWORD).first()

        if not verification:
            return Response(data={'verification': 'Forgot password request had not been sent. Send it please'},
                            status=status.HTTP_409_CONFLICT)

        if not verification.done:
            return Response(data={'verification': 'Verification is not done'},
                            status=status.HTTP_409_CONFLICT)

        user.set_password(request.data['new_password'])
        user.save()
        verification.delete()

        return Response(data={'message': 'Password has been changed successfully'}, status=status.HTTP_200_OK)


class UserChangeEmailView(APIView):
    def post(self, request):
        if 'email' not in request.data:
            return Response(data={'email': 'Field is not specified'}, status=status.HTTP_409_CONFLICT)

        try:
            validate_email(request.data['email'])
        except ValidationError:
            return Response(data={'email': 'Value does not matches email address pattern'},
                            status=status.HTTP_409_CONFLICT)

        if User.objects.filter(email=request.data['email']).exists():
            return Response(data={'email': 'User with this email is already exists'},
                            status=status.HTTP_409_CONFLICT)

        verification_code = get_random_string(length=8, allowed_chars='0123456789')

        send_mail(
            _('Verification email code'),
            verification_code,
            from_email=None,
            recipient_list=[request.data['email']],
            fail_silently=False
        )

        try:
            verification = EmailVerification.objects.get(user=self.request.user,
                                                         verification_type=EmailVerification.EMAIL)
            verification.new_value = request.data['email']
            verification.code = verification_code
            verification.save()
        except EmailVerification.DoesNotExist:
            EmailVerification.objects.create(user=self.request.user,
                                             verification_type=EmailVerification.EMAIL,
                                             code=verification_code,
                                             new_value=request.data['email'])

        return Response(data={'message': 'code_sent'}, status=status.HTTP_200_OK)


class UserChangeEmailVerificationView(APIView):
    def post(self, request):
        if 'code' not in request.data:
            return Response(data={'code': 'Field is not specified'}, status=status.HTTP_409_CONFLICT)

        verification = EmailVerification.objects.filter(user=self.request.user,
                                                        verification_type=EmailVerification.EMAIL).first()

        if not verification:
            return Response(data={'verification': 'Change email request had not been sent. Send it please'},
                            status=status.HTTP_409_CONFLICT)

        if int(request.data['code']) != verification.code:
            return Response(data={'code': 'Wrong code'},
                            status=status.HTTP_409_CONFLICT)

        self.request.user.email = verification.new_value
        self.request.user.save()

        verification.delete()

        return Response(data={'message': 'success'}, status=status.HTTP_200_OK)
