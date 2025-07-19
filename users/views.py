# users/views.py

from rest_framework import generics, permissions, status
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from rest_framework.serializers import ModelSerializer, CharField
from django.shortcuts import redirect
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.providers.oauth2.client import OAuth2Client
from dj_rest_auth.registration.views import SocialLoginView
from rest_framework.exceptions import ValidationError
import logging

User = get_user_model()

class UserSerializer(ModelSerializer):
    password = CharField(write_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password', 'first_name', 'last_name']

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance

class RegisterUserView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.AllowAny]

class UserProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user

# ✅ Google login with fallback to user creation
class CustomGoogleLogin(SocialLoginView):
    adapter_class = GoogleOAuth2Adapter
    client_class = OAuth2Client

    def post(self, request, *args, **kwargs):
        try:
            return super().post(request, *args, **kwargs)
        except ValidationError as e:
            errors = e.detail.get('non_field_errors', [])
            if errors and any("already registered" in str(err).lower() for err in errors):
                logging.warning("User already exists. Attempting login only.")
                return self._login_existing_user(request)
            elif errors and any("No user" in str(err) or "Unable to" in str(err) for err in errors):
                logging.info("No user found. Attempting auto-creation.")
                return self._create_new_user(request)
            raise e

    def _login_existing_user(self, request):
        self.serializer = self.get_serializer(data=request.data)
        self.serializer.is_valid(raise_exception=True)
        self.login()
        return Response(self.get_response_data(), status=status.HTTP_200_OK)

    def _create_new_user(self, request):
        self.serializer = self.get_serializer(data=request.data)
        self.serializer.is_valid(raise_exception=True)
        self.complete_social_login(self.request, self.serializer.validated_data['access_token'])
        self.login()
        return Response(self.get_response_data(), status=status.HTTP_201_CREATED)

def google_login_redirect(request):
    return redirect('/users/auth/social/login/google/')
