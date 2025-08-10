from django.contrib.auth import get_user_model
from rest_framework import status, viewsets, permissions
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.authtoken.models import Token
from django.shortcuts import get_object_or_404
from .throttles import LoginRateThrottle
import logging
import pyotp

from authentication.serializers import (
    UserRegistrationSerializer,
    UserProfileSerializer,
    AddressSerializer,
)
from authentication.models import Address
from users.tasks import send_verification_email

# Social login imports
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from dj_rest_auth.registration.views import SocialLoginView


class GoogleLogin(SocialLoginView):
    adapter_class = GoogleOAuth2Adapter


class UserRegistrationView(APIView):
    def post(self, request, *args, **kwargs):
        serializer = UserRegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        send_verification_email.delay(user.id)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    throttle_classes = [LoginRateThrottle]
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        email = request.data.get("email")
        password = request.data.get("password")

        User = get_user_model()
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            user = None

        if user and user.check_password(password) and user.email_verified:
            if user.is_paused:
                return Response(
                    {"detail": "Account is paused."},
                    status=status.HTTP_403_FORBIDDEN,
                )
            if user.is_staff:
                if not user.mfa_secret:
                    return Response(
                        {"detail": "Multi-factor authentication required."},
                        status=status.HTTP_403_FORBIDDEN,
                    )
                otp = request.data.get("otp")
                totp = pyotp.TOTP(user.mfa_secret)
                if not otp or not totp.verify(otp, valid_window=1):
                    return Response(
                        {"detail": "Invalid or missing OTP."},
                        status=status.HTTP_403_FORBIDDEN,
                    )
            token, _ = Token.objects.get_or_create(user=user)
            user_serializer = UserProfileSerializer(user)
            logging.info(f"User '{user.email}' logged in.")
            return Response(
                {"user": user_serializer.data, "tokens": {"access": token.key}},
                status=status.HTTP_200_OK,
            )

        if user and user.check_password(password) and not user.email_verified:
            return Response(
                {"detail": "Email not verified."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        logging.warning(f"Failed login attempt for email: {email}")
        return Response(
            {"detail": "Invalid credentials."}, status=status.HTTP_401_UNAUTHORIZED
        )


class UserProfileView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data)

    def put(self, request, *args, **kwargs):
        serializer = UserProfileSerializer(
            request.user, data=request.data, partial=True
        )
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
        return {"request": self.request}

    def perform_create(self, serializer):
        user = self.request.user
        data = self.request.data

        if data.get("is_default_shipping"):
            Address.objects.filter(user=user, is_default_shipping=True).update(
                is_default_shipping=False
            )

        if data.get("is_default_billing"):
            Address.objects.filter(user=user, is_default_billing=True).update(
                is_default_billing=False
            )

        serializer.save(user=user)

    def perform_update(self, serializer):
        user = self.request.user
        validated_data = serializer.validated_data

        if validated_data.get("is_default_shipping"):
            Address.objects.filter(user=user, is_default_shipping=True).exclude(
                id=serializer.instance.id
            ).update(is_default_shipping=False)

        if validated_data.get("is_default_billing"):
            Address.objects.filter(user=user, is_default_billing=True).exclude(
                id=serializer.instance.id
            ).update(is_default_billing=False)

        serializer.save()

    def perform_destroy(self, instance):
        if instance.is_default_shipping:
            logging.info(f"Removing default shipping status for address {instance.id}")
        if instance.is_default_billing:
            logging.info(f"Removing default billing status for address {instance.id}")
        instance.delete()


class VerifyEmailView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, token, *args, **kwargs):
        User = get_user_model()
        user = get_object_or_404(User, verification_token=token)
        user.email_verified = True
        user.verification_token = None
        user.save(update_fields=["email_verified", "verification_token"])
        return Response({"detail": "Email verified."}, status=status.HTTP_200_OK)
