# backend/urls.py

from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse

def home(request):
    return HttpResponse("Welcome to the e-commerce backend API!")

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home),
    path('users/', include('users.urls')),  # Users, including social login endpoints
    path('products/', include('products.urls')),
    path('orders/', include('orders.urls')),
    path('cart/', include('cart.urls')),
    path('payments/', include('payments.urls')),
    path('discounts/', include('discounts.urls')),
    path('reviews/', include('reviews.urls')),
    path('authentication/', include('authentication.urls')),

    # REST auth endpoints
    path('auth/', include('dj_rest_auth.urls')),  # login/logout/password reset
    path('auth/registration/', include('dj_rest_auth.registration.urls')),  # registration
    path('auth/social/', include('allauth.socialaccount.urls')),  # social login e.g. /auth/social/google/
]
