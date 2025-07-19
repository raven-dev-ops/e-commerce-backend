from django.contrib.auth import authenticate
from rest_framework import status, generics, mixins, viewsets
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.authtoken.models import Token
import logging

from authentication.serializers import (
    UserRegistrationSerializer,
    UserProfileSerializer,
    AddressSerializer,
)
from authentication.models import Address

# Social login imports
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from dj_rest_auth.registration.views import SocialLoginView


class GoogleLogin(SocialLoginView):
    adapter_class = GoogleOAuth2Adapter


class UserRegistrationView(APIView):
    def post(self, request, *args, **kwargs):
        serializer = UserRegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    def post(self, request, *args, **kwargs):
        email = request.data.get('email')
        password = request.data.get('password')

        user = authenticate(request, username=email, password=password)

        if user is not None:
            token, _ = Token.objects.get_or_create(user=user)
            user_serializer = UserProfileSerializer(user)
            logging.info(f"User '{user.email}' logged in.")
            return Response({
                "user": user_serializer.data,
                "tokens": {"access": token.key}
            }, status=status.HTTP_200_OK)

        logging.warning(f"Failed login attempt for email: {email}")
        return Response({"detail": "Invalid credentials."}, status=status.HTTP_401_UNAUTHORIZED)


class UserProfileView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data)

    def put(self, request, *args, **kwargs):
        serializer = UserProfileSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class AddressViewSet(viewsets.ModelViewSet):
    serializer_class = AddressSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Address.objects.filter(user=self.request.user)

    def get_serializer_context(self):
        return {'request': self.request}

    def perform_create(self, serializer):
        user = self.request.user
        data = self.request.data

        if data.get('is_default_shipping'):
            Address.objects.filter(user=user, is_default_shipping=True).update(is_default_shipping=False)

        if data.get('is_default_billing'):
            Address.objects.filter(user=user, is_default_billing=True).update(is_default_billing=False)

        serializer.save(user=user)

    def perform_update(self, serializer):
        user = self.request.user
        validated_data = serializer.validated_data

        if validated_data.get('is_default_shipping'):
            Address.objects.filter(user=user, is_default_shipping=True).exclude(id=serializer.instance.id).update(is_default_shipping=False)

        if validated_data.get('is_default_billing'):
            Address.objects.filter(user=user, is_default_billing=True).exclude(id=serializer.instance.id).update(is_default_billing=False)

        serializer.save()

    def perform_destroy(self, instance):
        if instance.is_default_shipping:
            logging.info(f"Removing default shipping status for address {instance.id}")
        if instance.is_default_billing:
            logging.info(f"Removing default billing status for address {instance.id}")
        instance.delete()
