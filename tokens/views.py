from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from django.conf import settings
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from django.urls import reverse
from users.models import User
from django.http import HttpResponse


class CustomTokenObtainPairView(TokenObtainPairView):
    def post(self, request, *args, **kwargs):
        """
        setting up two cookies: access and httponly refresh
        formatting response body
        """
        response = super().post(request, *args, **kwargs)

        response.set_cookie(
            key='access',
            value=response.data['access'],
            expires=settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'],
            secure=settings.SIMPLE_JWT['AUTH_COOKIE_SECURE'],
            httponly=False,
            samesite=settings.SIMPLE_JWT['AUTH_COOKIE_SAMESITE'],
        )

        response.set_cookie(
            key='refresh',
            value=response.data['refresh'],
            expires=settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'],
            secure=settings.SIMPLE_JWT['AUTH_COOKIE_SECURE'],
            httponly=settings.SIMPLE_JWT['AUTH_COOKIE_HTTP_ONLY'],
            samesite=settings.SIMPLE_JWT['AUTH_COOKIE_SAMESITE'],
            path=reverse('refresh')
        )

        response.data = {'access': response.data['access']}

        return response


class CustomTokenRefreshView(TokenRefreshView):
    def post(self, request, *args, **kwargs):
        if 'refresh' not in request.COOKIES:
            return Response({'refresh': 'The token has not been sent'}, status=status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer(data={'refresh': request.COOKIES['refresh']})

        try:
            serializer.is_valid(raise_exception=True)
        except TokenError as e:
            raise InvalidToken(e.args[0])

        response = Response(serializer.validated_data, status=status.HTTP_200_OK)

        response.set_cookie(
            key='access',
            value=serializer.validated_data['access'],
            expires=settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'],
            secure=settings.SIMPLE_JWT['AUTH_COOKIE_SECURE'],
            httponly=False,
            samesite=settings.SIMPLE_JWT['AUTH_COOKIE_SAMESITE']
        )

        return response


class LogoutView(APIView):
    def post(self, request):
        response = Response(status=status.HTTP_200_OK)

        response.delete_cookie('access',
                               samesite=settings.SIMPLE_JWT['AUTH_COOKIE_SAMESITE'])
        response.delete_cookie('refresh',
                               samesite=settings.SIMPLE_JWT['AUTH_COOKIE_SAMESITE'],
                               path='/api/token/refresh/')

        return response
