from rest_framework import generics
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.response import Response


class DiscountListCreateAPIView(generics.GenericAPIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request, *args, **kwargs):
        return Response([])

    def post(self, request, *args, **kwargs):
        return Response({"detail": "Discounts are no longer managed server-side."}, status=403)


class DiscountRetrieveUpdateDestroyAPIView(generics.GenericAPIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request, *args, **kwargs):
        return Response({"detail": "Discounts are no longer managed server-side."}, status=404)

    def put(self, request, *args, **kwargs):
        return Response({"detail": "Discounts are no longer managed server-side."}, status=403)

    def delete(self, request, *args, **kwargs):
        return Response({"detail": "Discounts are no longer managed server-side."}, status=403)


class CategoryListCreateAPIView(generics.GenericAPIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request, *args, **kwargs):
        return Response([])

    def post(self, request, *args, **kwargs):
        return Response({"detail": "Categories are no longer managed server-side."}, status=403)


class CategoryRetrieveUpdateDestroyAPIView(generics.GenericAPIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request, *args, **kwargs):
        return Response({"detail": "Categories are no longer managed server-side."}, status=404)

    def put(self, request, *args, **kwargs):
        return Response({"detail": "Categories are no longer managed server-side."}, status=403)

    def delete(self, request, *args, **kwargs):
        return Response({"detail": "Categories are no longer managed server-side."}, status=403)
