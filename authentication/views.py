# authentication/views.py

from django.contrib.auth import authenticate
from rest_framework import status, generics, mixins
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
from authentication.models import Address  # Adjust as needed


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
            return Response({
                "user": user_serializer.data,
                "tokens": {"access": token.key}  # Return the token string, not object
            }, status=status.HTTP_200_OK)

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


class AddressViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    generics.GenericAPIView
):
    serializer_class = AddressSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Address.objects(user=self.request.user.id)

    def perform_create(self, serializer):
        user = self.request.user
        data = self.request.data

        # Unset other default shipping addresses if this is default
        if data.get('is_default_shipping'):
            Address.objects(user=user.id, is_default_shipping=True).update(set__is_default_shipping=False)

        # Unset other default billing addresses if this is default
        if data.get('is_default_billing'):
            Address.objects(user=user.id, is_default_billing=True).update(set__is_default_billing=False)

        serializer.save(user=user)

    def perform_update(self, serializer):
        user = self.request.user
        validated_data = serializer.validated_data

        if validated_data.get('is_default_shipping'):
            Address.objects(user=user.id, is_default_shipping=True).update(set__is_default_shipping=False)

        if validated_data.get('is_default_billing'):
            Address.objects(user=user.id, is_default_billing=True).update(set__is_default_billing=False)

        serializer.save()

    def perform_destroy(self, instance):
        if instance.is_default_shipping:
            logging.info(f"Removing default shipping status for address {instance.id}")
        if instance.is_default_billing:
            logging.info(f"Removing default billing status for address {instance.id}")
        instance.delete()
