from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.helpers import complete_social_login
from allauth.socialaccount.models import SocialLogin
from allauth.socialaccount.providers.oauth2.client import OAuth2Client
from allauth.socialaccount.providers.oauth2.views import OAuth2LoginView
from allauth.socialaccount import app_settings
from allauth.socialaccount.adapter import get_adapter
from allauth.socialaccount.providers.google.provider import GoogleProvider
from allauth.socialaccount.providers.base import AuthError
from dj_rest_auth.registration.views import SocialLoginView
from django.contrib.auth import get_user_model

from .serializers import UserSerializer

User = get_user_model()


class RegisterUserView(generics.CreateAPIView):
    queryset = User.objects
    serializer_class = UserSerializer
    permission_classes = [permissions.AllowAny]


class UserProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


class CustomGoogleLogin(SocialLoginView):
    adapter_class = GoogleOAuth2Adapter
    callback_url = "https://twiinz-beard-frontend.netlify.app"
