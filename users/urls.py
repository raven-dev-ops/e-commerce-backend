from django.urls import path, include
from .views import RegisterUserView, UserProfileView

# Import social login views from dj_rest_auth
from dj_rest_auth.socialaccount.views import GoogleLogin
# Uncomment below for more providers
# from dj_rest_auth.socialaccount.views import FacebookLogin, InstagramLogin

urlpatterns = [
    path('register/', RegisterUserView.as_view(), name='register'),
    path('profile/', UserProfileView.as_view(), name='profile'),

    # REST auth endpoints (login, logout, password, etc)
    path('auth/', include('dj_rest_auth.urls')),

    # Registration endpoints (signup, verify, etc)
    path('auth/', include('dj_rest_auth.registration.urls')),

    # Social login endpoints for token POST (SPA-friendly)
    path('auth/google/', GoogleLogin.as_view(), name='google_login'),
    # path('auth/facebook/', FacebookLogin.as_view(), name='facebook_login'),  # Uncomment if you add Facebook
    # path('auth/instagram/', InstagramLogin.as_view(), name='instagram_login'),  # Uncomment if you add Instagram

    # (Optional) allauth browser-based social endpoints, usually not needed for REST/Spa
    # path('social/', include('allauth.socialaccount.urls')),
]
