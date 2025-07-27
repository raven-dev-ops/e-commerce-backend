# authentication/adapters.py

from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.exceptions import ImmediateHttpResponse
from allauth.account.utils import user_email
from django.http import JsonResponse

def get_user_model_ref():
    from django.contrib.auth import get_user_model
    return get_user_model()

class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    def pre_social_login(self, request, sociallogin):
        user = getattr(sociallogin.account, "user", None)

        if not user or not user_email(user):
            raise ImmediateHttpResponse(JsonResponse(
                {"error": "Social account is not linked to a valid user."},
                status=400
            ))

        email = user_email(user)

        try:
            existing_user = get_user_model_ref().objects.get(email=email)
            # Only connect if the email is verified
            if hasattr(existing_user, "emailaddress_set") and \
               existing_user.emailaddress_set.filter(email=email, verified=True).exists():
                sociallogin.connect(request, existing_user)
            # Else: skip connect, let Allauth create a new user
        except get_user_model_ref().DoesNotExist:
            # No user with this email exists, Allauth will create a new user
            pass
