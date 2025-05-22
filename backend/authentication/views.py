from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authentication import TokenAuthentication, BasicAuthentication
from rest_framework.permissions import IsAuthenticated

import logging # Keep logging import if you use it elsewhere
from rest_framework.authtoken.models import Token
from .serializers import UserRegistrationSerializer, UserProfileSerializer

from django.contrib.auth import authenticate # Import authenticate
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
            # Authentication successful, get or create token
            token, created = Token.objects.get_or_create(user=user)
            # Serialize the user data for the response
            user_serializer = UserProfileSerializer(user) # Use UserProfileSerializer for user data

            return Response({"user": user_serializer.data, "tokens": { "access": token }}, status=status.HTTP_200_OK)
        else:
            return Response({"detail": "Invalid credentials."}, status=status.HTTP_401_UNAUTHORIZED)

# Keep the existing UserProfileView as it seems you have custom update logic
class UserProfileView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data)

    def put(self, request, *args, **kwargs):
        serializer = UserProfileSerializer(request.user, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

from .models import Address
from .serializers import AddressSerializer
from rest_framework import generics

class AddressViewSet(generics.ListCreateAPIView, generics.RetrieveUpdateDestroyAPIView):
    queryset = Address.objects.all()
    serializer_class = AddressSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return Address.objects.none()  # Return empty queryset for unauthenticated users
        # Filter addresses by the current user
        return Address.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def perform_update(self, serializer):
        validated_data = serializer.validated_data
        user = self.request.user

        # Unset other default shipping addresses for the user
        if validated_data.get('is_default_shipping'):
            Address.objects(user=user, is_default_shipping=True).update(set__is_default_shipping=False)

        # Unset other default billing addresses for the user
        if validated_data.get('is_default_billing'):
            Address.objects(user=user, is_default_billing=True).update(set__is_default_billing=False)

        super().perform_update(serializer)

    def perform_create(self, serializer):
        # Perform the update logic first to handle default flags correctly
        self.perform_update(serializer)

    def perform_destroy(self, instance):
        # Check if the address being deleted is a default
        if instance.is_default_shipping:
            logging.info(f"Removing default shipping status for address {instance.id}")
        if instance.is_default_billing:
            logging.info(f"Removing default billing status for address {instance.id}")
        super().perform_destroy(instance)
