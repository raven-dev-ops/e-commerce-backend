from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.utils.translation import gettext as _

from .models import Cart, CartItem
from .serializers import CartItemSerializer


class CartView(APIView):
    permission_classes = [IsAuthenticated]

    def get_cart(self, user):
        cart = Cart.objects(user_id=str(user.id)).first()
        if not cart:
            cart = Cart.objects.create(user_id=str(user.id))
        return cart

    def get(self, request):
        cart = self.get_cart(request.user)
        items = CartItem.objects(cart=cart)
        serializer = CartItemSerializer(items, many=True)
        return Response(serializer.data)

    def post(self, request):
        """
        Add item to cart or update quantity if already present.
        Expects JSON:
        {
            "product_id": "some-product-id",
            "quantity": 1
        }
        """
        cart = self.get_cart(request.user)
        product_id = request.data.get("product_id")
        quantity = request.data.get("quantity", 1)

        if not product_id:
            return Response(
                {"detail": _("product_id is required")}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            quantity = int(quantity)
            if quantity < 1:
                return Response(
                    {"detail": _("quantity must be >= 1")},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        except ValueError:
            return Response(
                {"detail": _("quantity must be an integer")},
                status=status.HTTP_400_BAD_REQUEST,
            )

        item, created = CartItem.objects.get_or_create(cart=cart, product_id=product_id)
        if not created:
            item.quantity += quantity
        else:
            item.quantity = quantity
        item.save()

        serializer = CartItemSerializer(item)
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )

    def put(self, request):
        """
        Update quantity of a cart item.
        Expects JSON:
        {
            "product_id": "some-product-id",
            "quantity": 3
        }
        """
        cart = self.get_cart(request.user)
        product_id = request.data.get("product_id")
        quantity = request.data.get("quantity")

        if not product_id or quantity is None:
            return Response(
                {"detail": _("product_id and quantity are required")},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            quantity = int(quantity)
            if quantity < 1:
                return Response(
                    {"detail": _("quantity must be >= 1")},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        except ValueError:
            return Response(
                {"detail": _("quantity must be an integer")},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            item = CartItem.objects.get(cart=cart, product_id=product_id)
        except CartItem.DoesNotExist:
            return Response(
                {"detail": _("Item not found in cart")}, status=status.HTTP_404_NOT_FOUND
            )

        item.quantity = quantity
        item.save()
        serializer = CartItemSerializer(item)
        return Response(serializer.data)

    def delete(self, request):
        """
        Remove item from cart.
        Expects JSON:
        {
            "product_id": "some-product-id"
        }
        """
        cart = self.get_cart(request.user)
        product_id = request.data.get("product_id")

        if not product_id:
            return Response(
                {"detail": _("product_id is required")}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            item = CartItem.objects.get(cart=cart, product_id=product_id)
        except CartItem.DoesNotExist:
            return Response(
                {"detail": _("Item not found in cart")}, status=status.HTTP_404_NOT_FOUND
            )

        item.delete()
        return Response({"detail": _("Item removed")}, status=status.HTTP_204_NO_CONTENT)
