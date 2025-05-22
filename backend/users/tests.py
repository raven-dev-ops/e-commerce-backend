from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from rest_framework.authtoken.models import Token
from django.urls import reverse

# Get the custom user model
User = get_user_model()

# Create your tests here.

class UserModelTests(TestCase):

    def test_create_user_successfully(self):
        """
        Test creating a user with username, email, and password.
        """
        user = User.objects.create_user(username='testuser', email='test@example.com', password='testpassword')
        self.assertEqual(user.username, 'testuser')
        self.assertEqual(user.email, 'test@example.com')
        self.assertTrue(user.check_password('testpassword'))
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

class UserViewSetTests(APITestCase):
    def setUp(self):
        self.admin_user = User.objects.create_superuser(
            username='adminuser', email='admin@example.com', password='adminpassword'
        )
        self.regular_user = User.objects.create_user(
            username='regularuser', email='regular@example.com', password='regularpassword'
        )

        self.admin_token = Token.objects.create(user=self.admin_user)
        self.regular_user_token = Token.objects.create(user=self.regular_user)

        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.admin_token.key)
        self.user_list_url = reverse('user-list') # Assuming your user list URL name is 'user-list'

    def test_list_users_admin(self):
        """
        Ensure admin users can list all users.
        """
        response = self.client.get(self.user_list_url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2) # Should see admin and regular user

    def test_list_users_regular_user(self):
        """
        Ensure regular users cannot list all users.
        """
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.regular_user_token.key)
        response = self.client.get(self.user_list_url, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_retrieve_user_self(self):
        """
        Ensure a regular user can retrieve their own details.
        """
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.regular_user_token.key)
        url = reverse('user-detail', args=[self.regular_user.id]) # Assuming user detail URL name is 'user-detail'
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], self.regular_user.username)

    def test_retrieve_user_another_user_regular(self):
        """
        Ensure a regular user cannot retrieve another user's details.
        """
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.regular_user_token.key)
        url = reverse('user-detail', args=[self.admin_user.id])
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND) # Or 403 Forbidden depending on your permission logic

    def test_retrieve_user_admin(self):
        """
        Ensure an admin can retrieve any user's details.
        """
        url = reverse('user-detail', args=[self.regular_user.id])
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], self.regular_user.username)

    def test_update_user_self(self):
        """
        Ensure a regular user can update their own details.
        """
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.regular_user_token.key)
        url = reverse('user-detail', args=[self.regular_user.id])
        updated_data = {'first_name': 'UpdatedFirstName'}
        response = self.client.patch(url, updated_data, format='json') # Using PATCH for partial update
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.regular_user.refresh_from_db()
        self.assertEqual(self.regular_user.first_name, 'UpdatedFirstName')

    def test_update_user_another_user_regular(self):
        """
        Ensure a regular user cannot update another user's details.
        """
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.regular_user_token.key)
        url = reverse('user-detail', args=[self.admin_user.id])
        updated_data = {'first_name': 'Attempted Update'}
        response = self.client.patch(url, updated_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_user_admin(self):
        """
        Ensure an admin can update any user's details.
        """
        url = reverse('user-detail', args=[self.regular_user.id])
        updated_data = {'last_name': 'UpdatedLastName'}
        response = self.client.patch(url, updated_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.regular_user.refresh_from_db()
        self.assertEqual(self.regular_user.last_name, 'UpdatedLastName')

    def test_delete_user_admin(self):
        """
        Ensure an admin can delete a user.
        """
        url = reverse('user-detail', args=[self.regular_user.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(User.objects.count(), 1) # Only admin user should remain

    def test_delete_user_regular_user(self):
        """
        Ensure a regular user cannot delete another user.
        """
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.regular_user_token.key)
        url = reverse('user-detail', args=[self.admin_user.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(User.objects.count(), 2) # Users should not be deleted
    # You might need to adapt test_create_user_only_required_fields based on your actual user model's required fields.
    # For Django's default User model, username and password are required.
