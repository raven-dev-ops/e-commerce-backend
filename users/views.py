from functools import partial
from rest_framework import generics, permissions
from rest_framework.serializers import ModelSerializer, CharField
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.utils import timezone
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.providers.oauth2.client import OAuth2Client
from dj_rest_auth.registration.views import SocialLoginView
from orders.models import Order


def get_user_model_ref():
    from django.contrib.auth import get_user_model

    return get_user_model()


class UserSerializer(ModelSerializer):
    password = CharField(write_only=True)

    class Meta:
        model = get_user_model_ref()
        fields = [
            "id",
            "username",
            "email",
            "password",
            "first_name",
            "last_name",
            "avatar",
            "marketing_opt_in",
            "marketing_opt_in_at",
            "marketing_opt_out_at",
        ]
        read_only_fields = ["marketing_opt_in_at", "marketing_opt_out_at"]

    def create(self, validated_data):
        password = validated_data.pop("password")
        marketing_opt_in = validated_data.get("marketing_opt_in", False)
        user = get_user_model_ref()(**validated_data)
        if marketing_opt_in:
            user.marketing_opt_in_at = timezone.now()
            user.marketing_opt_out_at = None
        user.set_password(password)
        user.save()
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)
        marketing_opt_in = validated_data.pop("marketing_opt_in", None)
        if marketing_opt_in is not None and marketing_opt_in != instance.marketing_opt_in:
            instance.marketing_opt_in = marketing_opt_in
            now = timezone.now()
            if marketing_opt_in:
                instance.marketing_opt_in_at = now
                instance.marketing_opt_out_at = None
            else:
                instance.marketing_opt_out_at = now
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance


class RegisterUserView(generics.CreateAPIView):
    queryset = get_user_model_ref().objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.AllowAny]


class UserProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


class CustomGoogleLogin(SocialLoginView):
    adapter_class = GoogleOAuth2Adapter
    # partial ensures extra arguments don't conflict
    client_class = partial(OAuth2Client, scope_delimiter=" ")
    callback_url = "https://art-bay.netlify.app"


class UserDataExportView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user = request.user
        user_data = {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "phone_number": user.phone_number,
            "date_joined": user.date_joined.isoformat(),
        }

        orders = []
        for order in Order.objects.filter(user=user).prefetch_related("items"):
            orders.append(
                {
                    "id": order.id,
                    "created_at": order.created_at.isoformat(),
                    "total_price": str(order.total_price),
                    "status": order.status,
                    "items": [
                        {
                            "product_name": item.product_name,
                            "quantity": item.quantity,
                            "unit_price": str(item.unit_price),
                        }
                        for item in order.items.all()
                    ],
                }
            )

        data = {"user": user_data, "orders": orders, "reviews": []}
        response = Response(data)
        response["Content-Disposition"] = 'attachment; filename="user-data.json"'
        return response


class PauseUserView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def post(self, request, user_id, *args, **kwargs):
        user = get_object_or_404(get_user_model_ref(), id=user_id)
        user.is_paused = True
        user.save(update_fields=["is_paused"])
        return Response({"detail": "User paused."})


class ReactivateUserView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def post(self, request, user_id, *args, **kwargs):
        user = get_object_or_404(get_user_model_ref(), id=user_id)
        user.is_paused = False
        user.save(update_fields=["is_paused"])
        return Response({"detail": "User reactivated."})
