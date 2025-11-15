from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated


class CartView(APIView):
    """
    Cart operations are now handled entirely on the frontend.

    This view is kept only so the /cart/ endpoint exists and
    does not 500 while the backend no longer stores cart state.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        return Response([])

    def post(self, request, *args, **kwargs):
        return Response([])

    def put(self, request, *args, **kwargs):
        return Response([])

    def delete(self, request, *args, **kwargs):
        return Response([])
