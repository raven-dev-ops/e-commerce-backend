from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.decorators import action


class ProductViewSet(viewsets.GenericViewSet):
    """
    Products are now served entirely from the frontend's static catalog.

    This view keeps the /products/ routes alive but no longer reads
    from any backend product store.
    """

    permission_classes = [AllowAny]

    def list(self, request, *args, **kwargs):
        return Response({"count": 0, "results": []})

    @action(detail=False, methods=["get"], url_path="search")
    def search(self, request, *args, **kwargs):
        return Response([])
