# users/adapters.py

from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.account.utils import user_email, user_username
from allauth.account import app_settings
from allauth.account.adapter import get_adapter
from django.contrib.auth import get_user_model

class MySocialAccountAdapter(DefaultSocialAccountAdapter):
    def pre_social_login(self, request, sociallogin):
        """
        This hook is invoked after a successful authentication from the social provider,
        but before the login is actually processed.
        """
        user = sociallogin.user
        if not user.email:
            return  # Social account didn't provide email, can't link

        User = get_user_model()
        try:
            # Try to find a user with this email.
            existing_user = User.objects.get(email=user.email)
        except User.DoesNotExist:
            return  # No user with this email, normal social signup

        # If a user is found, connect this social account to the existing user
        sociallogin.connect(request, existing_user)
