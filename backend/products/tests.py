from django.test import TestCase
from mongoengine import connect, disconnect, ValidationError
from products.models import Product, Category
from products.serializers import ProductSerializer
from rest_framework.test import APITestCase
from rest_framework import status

# Create your tests here.
class ProductModelTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Connect to a test database
        cls.db_connection = connect('mongoenginetest', host='mongomock://localhost')

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        # Disconnect from the test database
        disconnect()

    def setUp(self):
        # Clear the database before each test
        Product.drop_collection()
        Category.drop_collection()

    def test_create_product_with_valid_data(self):
        product = Product(
            product_name='Test Product',
            category='Test Category',
            description='This is a test product.',
            price=19.99,
            ingredients=['Ingredient 1', 'Ingredient 2'],
            images=['image1.jpg', 'image2.png'],
            variations=[{'size': 'small', 'price': 18.00}],
            weight=0.5,
            dimensions='10x10x5',
            benefits=['Benefit 1', 'Benefit 2'],
            scent_profile='Floral',
            variants=[{'color': 'red', 'stock': 10}],
            tags=['test', 'product']
        )
        product.save()
        self.assertEqual(Product.objects.count(), 1)
        saved_product = Product.objects.first()
        self.assertEqual(saved_product.product_name, 'Test Product')
        self.assertEqual(saved_product.price, 19.99)
        self.assertListEqual(saved_product.ingredients, ['Ingredient 1', 'Ingredient 2'])

    def test_product_default_values(self):
        product = Product(product_name='Default Test')
        product.save()
        saved_product = Product.objects.first()
        self.assertTrue(saved_product.availability)
        self.assertEqual(saved_product.inventory, 0)
        self.assertEqual(saved_product.reserved_inventory, 0)
        self.assertEqual(saved_product.average_rating, 0.0)
        self.assertEqual(saved_product.review_count, 0)
        self.assertEqual(saved_product.variants, [])
        self.assertEqual(saved_product.tags, [])

    def test_product_str_method(self):
        product = Product(product_name='Awesome Widget')
        self.assertEqual(str(product), 'Awesome Widget')


    def test_create_category_with_valid_data(self):
        category = Category(name='Test Category')
        category.save()
        self.assertEqual(Category.objects.count(), 1)
        saved_category = Category.objects.first()
        self.assertEqual(saved_category.name, 'Test Category')
        self.assertIsNone(saved_category.description) # description is optional

    def test_create_category_without_name_raises_error(self):
        category = Category(description='Missing name')
        with self.assertRaises(ValidationError) as cm:
            category.save()
        self.assertIn('Field is required', str(cm.exception))

    def test_product_string_field_max_length(self):
        long_name = 'a' * 300
        product = Product(product_name=long_name)
        with self.assertRaises(ValidationError) as cm:
             # Save to trigger validation
            product.validate()
        self.assertIn('Field value is too long', str(cm.exception))

    def test_category_name_max_length(self):
        long_name = 'a' * 150
        category = Category(name=long_name)
        with self.assertRaises(ValidationError) as cm:
            # Save to trigger validation
            category.validate()
        self.assertIn('Field value is too long', str(cm.exception))

class ProductSerializerTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.db_connection = connect('mongoenginetest', host='mongomock://localhost')

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        disconnect()

    def setUp(self):
        Product.drop_collection()

    def test_product_serializer_serialization(self):
        product = Product(
            product_name='Serialized Product',
            category='Serialized Category',
            description='This product will be serialized.',
            price=25.50,
            ingredients=['Ing 1', 'Ing 2'],
            benefits=['Ben 1']
        )
        product.save() # Save to generate an _id for serialization
        serializer = ProductSerializer(instance=product)
        data = serializer.data

        self.assertIsNotNone(data.get('id'))
        self.assertEqual(data['product_name'], 'Serialized Product')
        self.assertEqual(data['category'], 'Serialized Category')
        self.assertEqual(data['description'], 'This product will be serialized.')
        self.assertEqual(float(data['price']), 25.50) # Price is DecimalField, compare float values
        self.assertListEqual(data['ingredients'], ['Ing 1', 'Ing 2'])
        self.assertListEqual(data['benefits'], ['Ben 1'])
        self.assertEqual(data['inventory'], 0) # Default value
        self.assertEqual(data['reserved_inventory'], 0) # Default value
        self.assertEqual(data['average_rating'], 0.0) # Default value, read-only
        self.assertEqual(data['review_count'], 0) # Default value, read-only

        # Check fields that have default values and should appear in serialization even if not set
        self.assertIn('availability', data) # Assuming default=True makes it appear
        self.assertIn('variants', data) # Assuming default=list makes it appear
        self.assertIn('tags', data) # Assuming required=False and potentially default makes it appear

    def test_product_serializer_deserialization_valid_data(self):
        valid_data = {
            'product_name': 'New Product',
            'category': 'New Category',
            'description': 'A new product for testing deserialization.',
            'price': '30.00', # Input as string, serializer handles DecimalField
            'ingredients': ['Ing A', 'Ing B', 'Ing C'],
            'benefits': ['Benefit X'],
            'inventory': 50,
            'reserved_inventory': 10,
            'scent_profile': 'Woody',
            'variants': ['variant1'],
            'tags': ['new', 'test'],
        }
        serializer = ProductSerializer(data=valid_data)
        self.assertTrue(serializer.is_valid())
        product = serializer.save() # DocumentSerializer.save() creates/updates a document

        self.assertIsNotNone(product.id)
        self.assertEqual(product.product_name, 'New Product')
        self.assertEqual(product.category, 'New Category')
        self.assertEqual(float(product.price), 30.00)
        self.assertListEqual(product.ingredients, ['Ing A', 'Ing B', 'Ing C'])
        self.assertEqual(product.inventory, 50)
        self.assertEqual(product.scent_profile, 'Woody')
        self.assertListEqual(product.variants, ['variant1'])
        self.assertListEqual(product.tags, ['new', 'test'])

    def test_product_serializer_missing_required_fields(self):
        invalid_data = {
            'category': 'Missing Name Category',
            'description': 'This should fail.',
            'price': '10.00',
            'ingredients': [],
            'benefits': [],
            'inventory': 5,
            'reserved_inventory': 1,
        }
        serializer = ProductSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('product_name', serializer.errors)
        self.assertEqual(serializer.errors['product_name'][0], 'This field is required.')

    def test_product_serializer_invalid_data_types(self):
        invalid_data = {
            'product_name': 'Invalid Type Test',
            'category': 'Invalid Category',
            'description': 'Testing invalid types.',
            'price': 'not a number', # Invalid type for price
            'ingredients': 'not a list', # Invalid type for ingredients
            'benefits': ['Valid Benefit'],
            'inventory': 10,
            'reserved_inventory': 2,
        }
        serializer = ProductSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('price', serializer.errors)
        self.assertIn('ingredients', serializer.errors)
        self.assertIn('A valid number is required.', str(serializer.errors['price'][0]))
        self.assertIn('Expected a list of items but got type', str(serializer.errors['ingredients'][0]))

    def test_product_serializer_max_length_constraints(self):
        invalid_data = {
            'product_name': 'A' * 300, # Exceeds max_length=255
            'category': 'B' * 150, # Exceeds max_length=100
            'description': 'Valid Description',
            'price': '5.00',
            'ingredients': [],
            'benefits': [],
            'inventory': 1,
            'reserved_inventory': 0,
        }
        serializer = ProductSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('product_name', serializer.errors)
        self.assertIn('category', serializer.errors)
        self.assertIn('Ensure this field has no more than 255 characters.', str(serializer.errors['product_name'][0]))
        self.assertIn('Ensure this field has no more than 100 characters.', str(serializer.errors['category'][0]))

    def test_product_serializer_scent_profile_allow_null_and_blank(self):
        valid_data_null = {
            'product_name': 'Null Scent Test', 'category': 'Test', 'description': '...', 'price': '1.00', 'ingredients': [], 'benefits': [], 'inventory': 1, 'reserved_inventory': 0, 'scent_profile': None
        }
        valid_data_blank = {
             'product_name': 'Blank Scent Test', 'category': 'Test', 'description': '...', 'price': '1.00', 'ingredients': [], 'benefits': [], 'inventory': 1, 'reserved_inventory': 0, 'scent_profile': ''
        }
        serializer_null = ProductSerializer(data=valid_data_null)
        self.assertTrue(serializer_null.is_valid())
        serializer_blank = ProductSerializer(data=valid_data_blank)
        self.assertTrue(serializer_blank.is_valid())

    def test_product_serializer_optional_fields_variants_tags(self):
        valid_data = {
            'product_name': 'Optional Fields Test', 'category': 'Test', 'description': '...', 'price': '1.00', 'ingredients': [], 'benefits': [], 'inventory': 1, 'reserved_inventory': 0
        } # variants and tags are missing
        serializer = ProductSerializer(data=valid_data)
        self.assertTrue(serializer.is_valid())

class ProductViewSetTests(APITestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.db_connection = connect('mongoenginetest', host='mongomock://localhost')

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        disconnect()

    def setUp(self):
        Product.drop_collection()
        # Create some test products
        Product.objects.create(product_name='Product 1', category='Cat A', description='Desc 1', price=10.00, ingredients=[], benefits=[], inventory=10, reserved_inventory=0)
        Product.objects.create(product_name='Product 2', category='Cat B', description='Desc 2', price=20.00, ingredients=[], benefits=[], inventory=20, reserved_inventory=0)

    def test_list_products(self):
        """
        Test retrieving a list of products.
        """
        url = '/api/products/'  # Assuming your products list URL is /api/products/
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)
        self.assertEqual(len(response.data), 2) # Assuming 2 products were created in setUp

    def test_retrieve_existing_product(self):
        """
        Test retrieving an existing product by its ID.
        """
        product = Product.objects.first()
        url = f'/api/products/{product.id}/'  # Assuming your product detail URL is /api/products/<id>/
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['product_name'], product.product_name)
        self.assertEqual(float(response.data['price']), float(product.price))

    def test_retrieve_non_existent_product(self):
        """
        Test retrieving a non-existent product.
        """
        # Use a valid-looking but non-existent ObjectId
        non_existent_id = '60c728f14f1a9c5b9c0e3e7b'
        url = f'/api/products/{non_existent_id}/'
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_create_product_with_valid_data(self):
        """
        Test creating a new product with valid data.
        """
        valid_data = {
            'product_name': 'New Product',
            'category': 'New Category',
            'description': 'A product created via API.',
            'price': '45.00',
            'ingredients': ['Ing X', 'Ing Y'],
            'benefits': ['Benefit A'],
            'inventory': 100,
            'reserved_inventory': 5,
        }
        url = '/api/products/'
        response = self.client.post(url, valid_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Product.objects.count(), 3) # Two initial + one created
        created_product = Product.objects.get(id=response.data['id'])
        self.assertEqual(created_product.product_name, 'New Product')
        self.assertEqual(float(created_product.price), 45.00)

    def test_create_product_with_invalid_data(self):
        """
        Test creating a new product with invalid data.
        """
        invalid_data = {
            'product_name': '', # Invalid - blank
            'category': 'Invalid Category',
            'description': 'This should fail.',
            'price': 'not a number', # Invalid type
            'ingredients': [],
            'benefits': [],
            'inventory': -10, # Invalid - negative
            'reserved_inventory': 0,
        }
        url = '/api/products/'
        response = self.client.post(url, invalid_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('product_name', response.data)
        self.assertIn('price', response.data)
        self.assertIn('inventory', response.data)
        self.assertEqual(Product.objects.count(), 2) # No new product should be created

    def test_update_existing_product_valid_data(self):
        """
        Test updating an existing product with valid data.
        """
        product = Product.objects.first()
        url = f'/api/products/{product.id}/'
        updated_data = {
            'product_name': 'Updated Product Name',
            'price': '99.99',
            'inventory': 5,
        }
        response = self.client.patch(url, updated_data, format='json') # Using PATCH for partial update

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        product.reload() # Reload product from database to get updated values
        self.assertEqual(product.product_name, 'Updated Product Name')
        self.assertEqual(float(product.price), 99.99)
        self.assertEqual(product.inventory, 5)

    def test_update_non_existent_product(self):
        """
        Test updating a non-existent product.
        """
        non_existent_id = '60c728f14f1a9c5b9c0e3e7b'
        url = f'/api/products/{non_existent_id}/'
        updated_data = {'product_name': 'Should not exist'}
        response = self.client.patch(url, updated_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_existing_product_invalid_data(self):
        """
        Test updating an existing product with invalid data.
        """
        product = Product.objects.first()
        url = f'/api/products/{product.id}/'
        invalid_data = {
            'price': 'not a number',
            'inventory': -50,
        }
        response = self.client.patch(url, invalid_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('price', response.data)
        self.assertIn('inventory', response.data)

    def test_delete_existing_product(self):
        """
        Test deleting an existing product.
        """
        product = Product.objects.first()
        url = f'/api/products/{product.id}/'
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Product.objects.count(), 1) # One product should be left
        with self.assertRaises(Product.DoesNotExist):
            Product.objects.get(id=product.id)

    def test_delete_non_existent_product(self):
        """
        Test deleting a non-existent product.
        """
        non_existent_id = '60c728f14f1a9c5b9c0e3e7b'
        url = f'/api/products/{non_existent_id}/'
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(Product.objects.count(), 2) # Number of products should not change

    # Add tests for filtering, searching, and pagination for the list action here
    # These will require creating more test data with varying categories, names, descriptions, etc.

    # Example placeholder for a filtering test:
    # def test_list_products_filter_by_category(self):
    #     # Create more products with different categories
    #     # Send GET request with ?category=Cat A
    #     # Assert that only products with category Cat A are returned
    #     pass