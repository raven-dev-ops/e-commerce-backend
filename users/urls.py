from django.urls import path, include
from .views import RegisterUserView, UserProfileView

# ✅ Imports for Google OAuth2
from dj_rest_auth.registration.views import SocialLoginView
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.providers.oauth2.client import OAuth2Client


# ✅ Google login integration
class GoogleLogin(SocialLoginView):
    adapter_class = GoogleOAuth2Adapter
    client_class = OAuth2Client
    # callback_url = 'https://twiinz-beard-frontend.netlify.app'  # Optional

urlpatterns = [
    # Local user endpoints
    path('register/', RegisterUserView.as_view(), name='register'),
    path('profile/', UserProfileView.as_view(), name='profile'),

    # dj-rest-auth default endpoints (login, logout, password reset)
    path('auth/', include('dj_rest_auth.urls')),

    # Registration endpoints (email verification, signup, etc.)
    path('auth/', include('dj_rest_auth.registration.urls')),

    # ✅ Google social login endpoint
    path('auth/google/', GoogleLogin.as_view(), name='google_login'),

    # Optional: Add these if needed later
    # path('auth/facebook/', FacebookLogin.as_view(), name='facebook_login'),
    # path('auth/instagram/', InstagramLogin.as_view(), name='instagram_login'),
    # path('social/', include('allauth.socialaccount.urls')),  # For browser-based flows
]
