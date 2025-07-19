# users/urls.py

from django.urls import path, include
from .views import RegisterUserView, UserProfileView, CustomGoogleLogin

urlpatterns = [
    path('register/', RegisterUserView.as_view(), name='register'),
    path('profile/', UserProfileView.as_view(), name='profile'),

    # Auth endpoints
    path('auth/', include('dj_rest_auth.urls')),  # login/logout/password reset
    path('auth/registration/', include('dj_rest_auth.registration.urls')),  # signup/email verification

    # Custom Google login endpoint
    path('auth/google/', CustomGoogleLogin.as_view(), name='google_login'),
]
