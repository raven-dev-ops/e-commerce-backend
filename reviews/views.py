# reviews/views.py

from rest_framework.viewsets import GenericViewSet
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication


class ReviewViewSet(GenericViewSet):
    """
    Reviews are no longer stored on the backend; this API is effectively disabled.
    Kept only so the routes exist and return a clear message instead of 500s.
    """

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def list(self, request, *args, **kwargs):
        return Response([], status=status.HTTP_200_OK)

    def create(self, request, *args, **kwargs):
        return Response(
            {"detail": "Reviews are no longer stored on the server."},
            status=status.HTTP_403_FORBIDDEN,
        )

    def update(self, request, pk=None, *args, **kwargs):
        return Response(
            {"detail": "Reviews are no longer stored on the server."},
            status=status.HTTP_403_FORBIDDEN,
        )

    def destroy(self, request, pk=None, *args, **kwargs):
        return Response(
            {"detail": "Reviews are no longer stored on the server."},
            status=status.HTTP_403_FORBIDDEN,
        )
