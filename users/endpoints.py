from django.urls import path, include
from .views import (
    RegisterUserView,
    UserProfileView,
    CustomGoogleLogin,
    UserDataExportView,
    PauseUserView,
    ReactivateUserView,
)

urlpatterns = [
    path("register/", RegisterUserView.as_view(), name="register"),
    path("profile/", UserProfileView.as_view(), name="profile"),
    path("auth/", include("dj_rest_auth.urls")),
    path("auth/registration/", include("dj_rest_auth.registration.urls")),
    path("auth/google/", CustomGoogleLogin.as_view(), name="google_login"),
    path("export/", UserDataExportView.as_view(), name="user-data-export"),
    path("<int:user_id>/pause/", PauseUserView.as_view(), name="pause-user"),
    path(
        "<int:user_id>/reactivate/",
        ReactivateUserView.as_view(),
        name="reactivate-user",
    ),
]
