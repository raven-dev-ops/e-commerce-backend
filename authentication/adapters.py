from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.exceptions import ImmediateHttpResponse
from allauth.account.utils import user_email
from django.contrib.auth import get_user_model
from django.http import JsonResponse

User = get_user_model()

class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    def pre_social_login(self, request, sociallogin):
        user = getattr(sociallogin.account, "user", None)

        if not user or not user_email(user):
            # Prevent crash when user object is missing
            raise ImmediateHttpResponse(JsonResponse(
                {"error": "Social account is not linked to a valid user."},
                status=400
            ))

        email = user_email(user)

        try:
            existing_user = User.objects.get(email=email)
            sociallogin.connect(request, existing_user)
        except User.DoesNotExist:
            # Continue with normal signup flow
            pass
