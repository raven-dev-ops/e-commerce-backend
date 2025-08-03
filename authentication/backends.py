from django.contrib.auth.backends import BaseBackend


def get_user_model_ref():
    from django.contrib.auth import get_user_model

    return get_user_model()


class MongoEngineBackend(BaseBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            user = get_user_model_ref().objects.get(username=username)
            if user.check_password(password):
                return user
        except get_user_model_ref().DoesNotExist:
            return None

    def get_user(self, user_id):
        try:
            return get_user_model_ref().objects.get(id=user_id)
        except get_user_model_ref().DoesNotExist:
            return None
