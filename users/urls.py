from django.urls import path, include
from .views import RegisterUserView, UserProfileView

# ✅ Correct imports for Google social login
from dj_rest_auth.registration.views import SocialLoginView
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.providers.oauth2.client import OAuth2Client

# Optional: Uncomment and configure if you want to support other social providers
# from allauth.socialaccount.providers.facebook.views import FacebookOAuth2Adapter
# from allauth.socialaccount.providers.instagram.views import InstagramOAuth2Adapter

# ✅ Social login class for Google
class GoogleLogin(SocialLoginView):
    adapter_class = GoogleOAuth2Adapter
    client_class = OAuth2Client
    # Optional: Set callback_url if needed
    # callback_url = 'https://yourdomain.com/auth/google/callback/'

# Optional classes for other providers
# class FacebookLogin(SocialLoginView):
#     adapter_class = FacebookOAuth2Adapter
#     client_class = OAuth2Client

# class InstagramLogin(SocialLoginView):
#     adapter_class = InstagramOAuth2Adapter
#     client_class = OAuth2Client

urlpatterns = [
    path('register/', RegisterUserView.as_view(), name='register'),
    path('profile/', UserProfileView.as_view(), name='profile'),

    # REST auth endpoints (login, logout, password reset, etc)
    path('auth/', include('dj_rest_auth.urls')),

    # Registration endpoints (signup, email verification, etc)
    path('auth/', include('dj_rest_auth.registration.urls')),

    # Social login endpoint for Google
    path('auth/google/', GoogleLogin.as_view(), name='google_login'),

    # Optional: Add these if you define Facebook/Instagram login views
    # path('auth/facebook/', FacebookLogin.as_view(), name='facebook_login'),
    # path('auth/instagram/', InstagramLogin.as_view(), name='instagram_login'),

    # Optional: Allauth browser-based social login (usually not needed for SPA)
    # path('social/', include('allauth.socialaccount.urls')),
]
