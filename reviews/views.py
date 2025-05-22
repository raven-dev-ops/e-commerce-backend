# reviews/views.py

from rest_framework.viewsets import ViewSet
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from rest_framework.decorators import action

from mongoengine.queryset.visitor import Q

from .models import Review
from products.models import Product
from authentication.models import User
from .serializers import ReviewSerializer


class ReviewViewSet(ViewSet):
    serializer_class = ReviewSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def create(self, request):
        user = request.user
        product_id = request.data.get('product_id')
        rating = request.data.get('rating')
        comment = request.data.get('comment')

        if not product_id or rating is None:
            return Response({"detail": "product_id and rating are required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            rating = int(rating)
            if not 1 <= rating <= 5:
                raise ValueError
        except (ValueError, TypeError):
            return Response({"detail": "Rating must be an integer between 1 and 5."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return Response({"detail": "Product not found."}, status=status.HTTP_404_NOT_FOUND)

        existing_review = Review.objects.filter(user=user.id, product=product.id).first()
        if existing_review:
            return Response({"detail": "You have already reviewed this product."}, status=status.HTTP_400_BAD_REQUEST)

        review = Review(
            user=user.id,
            product=product.id,
            rating=rating,
            comment=comment
        )
        review.status = 'pending'
        review.save()

        product.review_count += 1
        product.save()

        serializer = ReviewSerializer(review)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def list(self, request):
        product_id = request.query_params.get('product_id')
        is_admin = request.user.is_staff if hasattr(request.user, 'is_staff') else False

        reviews_queryset = Review.objects

        if not product_id:
            return Response({"detail": "product_id query parameter is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return Response({"detail": "Product not found."}, status=status.HTTP_404_NOT_FOUND)

        reviews_queryset = reviews_queryset.filter(product=product_id)
        if not is_admin:
            reviews_queryset = reviews_queryset.filter(status='approved')

        reviews = reviews_queryset.order_by('-created_at')
        serializer = ReviewSerializer(reviews, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def update(self, request, pk=None):
        user = request.user
        is_admin = request.user.is_staff if hasattr(request.user, 'is_staff') else False

        try:
            review = Review.objects.get(id=pk)
            old_review = Review.objects.get(id=pk)
        except Review.DoesNotExist:
            return Response({"detail": "Review not found."}, status=status.HTTP_404_NOT_FOUND)

        if str(review.user.id) != str(user.id) and not is_admin:
            return Response({"detail": "You do not have permission to edit this review."}, status=status.HTTP_403_FORBIDDEN)

        rating = request.data.get('rating')
        comment = request.data.get('comment')

        old_rating = old_review.rating
        old_status = old_review.status

        if rating is not None:
            try:
                rating = int(rating)
                if not 1 <= rating <= 5:
                    raise ValueError
                review.rating = rating
            except (ValueError, TypeError):
                return Response({"detail": "Rating must be an integer between 1 and 5."}, status=status.HTTP_400_BAD_REQUEST)

        if comment is not None:
            review.comment = comment

        review.save()

        product = review.product.fetch()

        if old_status == 'approved' and review.status == 'approved':
            if product.approved_review_count > 0:
                product.average_rating = ((product.average_rating * product.approved_review_count) - old_rating + review.rating) / product.approved_review_count
        elif old_status != 'approved' and review.status == 'approved':
            if product.approved_review_count == 0:
                product.average_rating = review.rating
            else:
                product.average_rating = ((product.average_rating * product.approved_review_count) + review.rating) / (product.approved_review_count + 1)
            product.approved_review_count += 1
        elif old_status == 'approved' and review.status != 'approved':
            if product.approved_review_count > 1:
                product.average_rating = ((product.average_rating * product.approved_review_count) - old_rating) / (product.approved_review_count - 1)
            else:
                product.average_rating = 0.0
            product.approved_review_count -= 1

        product.save()
        serializer = ReviewSerializer(review)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def destroy(self, request, pk=None):
        user = request.user
        is_admin = request.user.is_staff if hasattr(request.user, 'is_staff') else False

        try:
            review = Review.objects.get(id=pk)
        except Review.DoesNotExist:
            return Response({"detail": "Review not found."}, status=status.HTTP_404_NOT_FOUND)

        if str(review.user.id) != str(user.id) and not is_admin:
            return Response({"detail": "You do not have permission to delete this review."}, status=status.HTTP_403_FORBIDDEN)

        product = review.product.fetch()

        if review.status == 'approved':
            if product.approved_review_count > 1:
                product.average_rating = ((product.average_rating * product.approved_review_count) - review.rating) / (product.approved_review_count - 1)
            else:
                product.average_rating = 0.0
            product.approved_review_count -= 1

        product.review_count -= 1
        product.save()

        review.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post'])
    def moderate(self, request, pk=None):
        is_admin = request.user.is_staff if hasattr(request.user, 'is_staff') else False
        if not is_admin:
            return Response({"detail": "You do not have permission to moderate reviews."}, status=status.HTTP_403_FORBIDDEN)

        try:
            review = Review.objects.get(id=pk)
        except Review.DoesNotExist:
            return Response({"detail": "Review not found."}, status=status.HTTP_404_NOT_FOUND)

        new_status = request.data.get('status')
        if new_status not in ['approved', 'rejected']:
            return Response({"detail": "Invalid status. Status must be 'approved' or 'rejected'."}, status=status.HTTP_400_BAD_REQUEST)

        old_status = review.status
        review.status = new_status
        review.save()

        product = review.product.fetch()

        if old_status != 'approved' and new_status == 'approved':
            if product.approved_review_count == 0:
                product.average_rating = review.rating
            else:
                product.average_rating = ((product.average_rating * product.approved_review_count) + review.rating) / (product.approved_review_count + 1)
            product.approved_review_count += 1
        elif old_status == 'approved' and new_status != 'approved':
            if product.approved_review_count > 1:
                product.average_rating = ((product.average_rating * product.approved_review_count) - review.rating) / (product.approved_review_count - 1)
            else:
                product.average_rating = 0.0
            product.approved_review_count -= 1

        product.save()
        serializer = ReviewSerializer(review)
        return Response(serializer.data, status=status.HTTP_200_OK)
