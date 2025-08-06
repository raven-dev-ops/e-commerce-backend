# reviews/views.py

from rest_framework.viewsets import GenericViewSet
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.pagination import PageNumberPagination
from rest_framework.decorators import action
from django.utils.translation import gettext as _

from .throttles import ReviewCreateThrottle

from .models import Review
from products.models import Product
from .serializers import ReviewSerializer


class ReviewPagination(PageNumberPagination):
    page_size = 10


class ReviewViewSet(GenericViewSet):
    serializer_class = ReviewSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    pagination_class = ReviewPagination
    throttle_classes = [ReviewCreateThrottle]

    def get_throttles(self):
        if getattr(self, "action", None) == "create":
            return [throttle() for throttle in self.throttle_classes]
        return []

    def create(self, request):
        user = request.user
        product_id = request.data.get("product_id")
        rating = request.data.get("rating")
        comment = request.data.get("comment")

        if not product_id or rating is None:
            return Response(
                {"detail": _("product_id and rating are required.")},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            rating = int(rating)
            if not 1 <= rating <= 5:
                raise ValueError
        except (ValueError, TypeError):
            return Response(
                {"detail": _("Rating must be an integer between 1 and 5.")},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            product = Product.objects.get(pk=product_id)
        except Product.DoesNotExist:
            return Response(
                {"detail": _("Product not found.")}, status=status.HTTP_404_NOT_FOUND
            )

        existing_review = Review.objects.filter(
            user_id=user.id, product=product
        ).first()
        if existing_review:
            return Response(
                {"detail": _("You have already reviewed this product.")},
                status=status.HTTP_400_BAD_REQUEST,
            )

        review = Review(
            user_id=user.id, product=product, rating=rating, comment=comment
        )
        review.status = "pending"
        review.save()
        product.add_review(review.rating, review.status)

        serializer = ReviewSerializer(review)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def list(self, request):
        product_id = request.query_params.get("product_id")
        is_admin = request.user.is_staff if hasattr(request.user, "is_staff") else False

        if not product_id:
            return Response(
                {"detail": _("product_id query parameter is required.")},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            Product.objects.get(pk=product_id)
        except Product.DoesNotExist:
            return Response(
                {"detail": _("Product not found.")}, status=status.HTTP_404_NOT_FOUND
            )

        reviews_queryset = Review.objects.filter(product=product_id)
        if not is_admin:
            reviews_queryset = reviews_queryset.filter(status="approved")

        reviews_queryset = reviews_queryset.order_by("-created_at")
        page = self.paginate_queryset(reviews_queryset)
        if page is not None:
            serializer = ReviewSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = ReviewSerializer(reviews_queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def update(self, request, pk=None):
        user = request.user
        is_admin = request.user.is_staff if hasattr(request.user, "is_staff") else False

        try:
            review = Review.objects.get(id=pk)
        except Review.DoesNotExist:
            return Response(
                {"detail": _("Review not found.")}, status=status.HTTP_404_NOT_FOUND
            )

        if review.user_id != user.id and not is_admin:
            return Response(
                {"detail": _("You do not have permission to edit this review.")},
                status=status.HTTP_403_FORBIDDEN,
            )

        old_rating = review.rating
        old_status = review.status

        rating = request.data.get("rating")
        comment = request.data.get("comment")

        if rating is not None:
            try:
                rating = int(rating)
                if not 1 <= rating <= 5:
                    raise ValueError
                review.rating = rating
            except (ValueError, TypeError):
                return Response(
                    {"detail": _("Rating must be an integer between 1 and 5.")},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        if comment is not None:
            review.comment = comment

        review.save()

        product = review.product
        product.update_review(old_rating, review.rating, old_status, review.status)
        serializer = ReviewSerializer(review)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def destroy(self, request, pk=None):
        user = request.user
        is_admin = request.user.is_staff if hasattr(request.user, "is_staff") else False

        try:
            review = Review.objects.get(id=pk)
        except Review.DoesNotExist:
            return Response(
                {"detail": _("Review not found.")}, status=status.HTTP_404_NOT_FOUND
            )

        if review.user_id != user.id and not is_admin:
            return Response(
                {"detail": _("You do not have permission to delete this review.")},
                status=status.HTTP_403_FORBIDDEN,
            )

        product = review.product
        product.remove_review(review.rating, review.status)

        review.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=["post"])
    def moderate(self, request, pk=None):
        is_admin = request.user.is_staff if hasattr(request.user, "is_staff") else False
        if not is_admin:
            return Response(
                {"detail": _("You do not have permission to moderate reviews.")},
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            review = Review.objects.get(id=pk)
        except Review.DoesNotExist:
            return Response(
                {"detail": _("Review not found.")}, status=status.HTTP_404_NOT_FOUND
            )

        new_status = request.data.get("status")
        if new_status not in ["approved", "rejected"]:
            return Response(
                {"detail": _("Invalid status. Status must be 'approved' or 'rejected'.")},
                status=status.HTTP_400_BAD_REQUEST,
            )

        old_status = review.status
        review.status = new_status
        review.save()

        product = review.product
        product.update_review(review.rating, review.rating, old_status, new_status)
        serializer = ReviewSerializer(review)
        return Response(serializer.data, status=status.HTTP_200_OK)
