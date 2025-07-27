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
        user = getattr(sociallogin, "user", None)
        if not user or not user_email(user):
            logger.warning(f"Social login has no user or user has no email attached. sociallogin.user: {user}")
            raise ImmediateHttpResponse(JsonResponse(
                {"error": "Social account is not linked to a valid user."},
                status=400
            ))

        email = user_email(user)
        try:
            existing_user = get_user_model_ref().objects.get(email=email)
            logger.info(f"Found existing user with email {email}, connecting social login.")
            # Lenient: connect regardless of verified email addresses
            sociallogin.connect(request, existing_user)
        except get_user_model_ref().DoesNotExist:
            logger.info(f"No existing user with email {email}. Proceeding with new user signup.")
            # Let signup continue normally
            pass
