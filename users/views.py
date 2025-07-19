from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.serializers import CharField
from allauth.socialaccount.models import SocialAccount
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.helpers import complete_social_login
from allauth.socialaccount import requests as allauth_requests
from allauth.socialaccount.providers.oauth2.client import OAuth2Error
from django.conf import settings

from .serializers import UserSerializer
from .models import User


class RegisterUserView(generics.CreateAPIView):
    queryset = User.objects
    serializer_class = UserSerializer
    permission_classes = [permissions.AllowAny]


class UserProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


class CustomGoogleLogin(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        code = request.data.get("code")
        if not code:
            return Response({"error": "Missing authorization code"}, status=400)

        adapter = GoogleOAuth2Adapter()
        app = adapter.get_provider().get_app(request)
        client = adapter.get_client(request, app)
        callback_url = "https://twiinz-beard-frontend.netlify.app"  # Must match the one in Google Console

        try:
            token = client.get_access_token(code)
            login = adapter.complete_login(request, app, token)
            login.token = token
            login.state = SocialAccount.state_from_request(request)
            complete_social_login(request, login)

            if not login.is_existing:
                login.user.save()

            return Response({
                "key": str(token.token),
                "email": login.user.email,
                "username": login.user.username
            })

        except OAuth2Error as e:
            return Response({"detail": "OAuth error", "error": str(e)}, status=400)
