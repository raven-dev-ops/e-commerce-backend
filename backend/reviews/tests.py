# reviews/tests.py

from rest_framework.test import APITestCase
from rest_framework import status
from authentication.models import User
from reviews.models import Review
from products.models import Product
from rest_framework.authtoken.models import Token

class ReviewViewSetTestCase(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.product = Product.objects.create(name='Test Product', description='A test product', price=10.0)
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)
        self.review_list_url = '/reviews/' # Assuming your reviews list endpoint is at /reviews/

    def test_create_review_successfully(self):
        data = {
            'product_id': str(self.product.id),
            'rating': 4,
            'comment': 'This is a great product!'
        }
        response = self.client.post(self.review_list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Review.objects.count(), 1)
        review = Review.objects.get()
        self.assertEqual(str(review.product.id), data['product_id'])
        self.assertEqual(review.rating, data['rating'])
        self.assertEqual(review.comment, data['comment'])
        self.assertEqual(review.status, 'pending')
        self.assertEqual(str(review.user.id), str(self.user.id))


    def test_create_review_with_invalid_rating(self):
        data = {
            'product_id': str(self.product.id),
            'rating': 0,  # Invalid rating
            'comment': 'This review has an invalid rating.'
        }
        response = self.client.post(self.review_list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Review.objects.count(), 0)

        data['rating'] = 6 # Another invalid rating
        response = self.client.post(self.review_list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Review.objects.count(), 0)