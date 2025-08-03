from functools import partial
from rest_framework import generics, permissions
from rest_framework.serializers import ModelSerializer, CharField
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.providers.oauth2.client import OAuth2Client
from dj_rest_auth.registration.views import SocialLoginView


def get_user_model_ref():
    from django.contrib.auth import get_user_model

    return get_user_model()


class UserSerializer(ModelSerializer):
    password = CharField(write_only=True)

    class Meta:
        model = get_user_model_ref()
        fields = ["id", "username", "email", "password", "first_name", "last_name"]

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
