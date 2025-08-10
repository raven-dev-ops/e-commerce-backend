from functools import partial
from rest_framework import generics, permissions
from rest_framework.serializers import ModelSerializer, CharField
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.providers.oauth2.client import OAuth2Client
from dj_rest_auth.registration.views import SocialLoginView
from orders.models import Order
from reviews.models import Review


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
        ]

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = get_user_model_ref()(**validated_data)
        user.set_password(password)
        user.save()
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)
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
    callback_url = "https://twiinz-beard-frontend.netlify.app"


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

        reviews = []
        for review in Review.objects.filter(user_id=user.id):
            product_name = (
                review.product.product_name
                if getattr(review, "product", None)
                else None
            )
            reviews.append(
                {
                    "product": product_name,
                    "rating": review.rating,
                    "comment": review.comment,
                    "status": review.status,
                    "created_at": review.created_at.isoformat(),
                }
            )

        data = {"user": user_data, "orders": orders, "reviews": reviews}
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
