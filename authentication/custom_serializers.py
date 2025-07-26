# authentication/custom_serializers.py

from dj_rest_auth.registration.serializers import SocialLoginSerializer
from allauth.socialaccount.providers.oauth2.client import OAuth2Client

class CustomSocialLoginSerializer(SocialLoginSerializer):
    """
    Construct OAuth2Client without accidentally passing scope_delimiter twice.
    """
    client_class = OAuth2Client

    def validate(self, attrs):
        request = self.context['request']
        adapter = self.get_adapter()
        provider = adapter.get_provider()
        app      = provider.get_app(request)

        # Build OAuth2Client with exactly one scope_delimiter
        client = self.client_class(
            request=request,
            client_id=app.client_id,
            secret=app.secret,
            scope=provider.get_scope(),
            # note: do NOT re‑pass scope_delimiter here
        )

        # Let the adapter finish the login flow
        social_login = adapter.complete_social_login(request, client, data=attrs)
        self.perform_authentication(social_login)

        return attrs
