from rest_framework import serializers


def get_user_model_ref():
    from django.contrib.auth import get_user_model

    return get_user_model()


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = get_user_model_ref()
        fields = [
            "id",
            "username",
            "email",
            "password",
            "first_name",
            "last_name",
            "phone_number",
        ]

    def create(self, validated_data):
        user_model = get_user_model_ref()
        password = validated_data.pop("password")
        user = user_model(**validated_data)
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
