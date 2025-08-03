from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AddressViewSet, UserRegistrationView, LoginView, GoogleLogin

router = DefaultRouter()
router.register(r"addresses", AddressViewSet, basename="address")

urlpatterns = [
    path("register/", UserRegistrationView.as_view(), name="register"),
    path("login/", LoginView.as_view(), name="login"),
    path("auth/google/login/", GoogleLogin.as_view(), name="google_login"),
    path("", include(router.urls)),
]
