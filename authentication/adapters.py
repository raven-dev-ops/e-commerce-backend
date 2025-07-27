# authentication/adapters.py

import logging
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.exceptions import ImmediateHttpResponse
from allauth.account.utils import user_email
from django.http import JsonResponse

logger = logging.getLogger(__name__)

def get_user_model_ref():
    from django.contrib.auth import get_user_model
    return get_user_model()

class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    def pre_social_login(self, request, sociallogin):
        user = getattr(sociallogin.account, "user", None)
        if not user:
            logger.warning("Social login has no user attached")
            raise ImmediateHttpResponse(JsonResponse(
                {"error": "Social account is not linked to a valid user."},
                status=400
            ))

        email = user_email(user)
        if not email:
            logger.warning("Social login user has no email")
            raise ImmediateHttpResponse(JsonResponse(
                {"error": "Social account is missing email."},
                status=400
            ))

        try:
            existing_user = get_user_model_ref().objects.get(email=email)
            logger.info(f"Connecting social account to existing user {existing_user}")
            sociallogin.connect(request, existing_user)
        except get_user_model_ref().DoesNotExist:
            logger.info(f"No existing user with email {email}, allowing signup")

