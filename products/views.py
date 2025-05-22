from rest_framework import status
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet
from products.models import Product
from products.filters import ProductFilter
from products.serializers import ProductSerializer
from bson.objectid import ObjectId
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter
from rest_framework.pagination import PageNumberPagination

# Create your views here.
class ProductViewSet(ViewSet):
    def list(self, request):
        """
        List all products.

        Retrieves all Product documents from MongoDB and serializes them.

        Args:
            request: The incoming request object.
        """
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_class = ProductFilter
    search_fields = ['product_name', 'description', 'tags', 'category']

    def list(self, request):
        # Note: Filtering, searching, and pagination will be applied automatically
        # by DRF and the configured backends when calling Product.objects.all()
        # or a similar queryset method within a DRF view/viewset that uses
        # filter_backends and pagination_class.
        # Retrieve all Product objects using mongoengine
        products = Product.objects.all()
        serializer = ProductSerializer(products, many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk=None):
        try:
            product = Product.objects.get(id=ObjectId(pk))
            serializer = ProductSerializer(product) # Serialize the single product
            return Response(serializer.data)
        except Product.DoesNotExist:
            # Return 404 if the product with the given ObjectId does not exist
            return Response(status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            # Handle other potential exceptions during ObjectId conversion or retrieval
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def create(self, request):
        """
        Create a new product.

        Deserializes the incoming data, saves a new Product document to MongoDB,
        and returns the serialized created product.

        Args:
            request: The incoming request object containing product data.
        """
        serializer = ProductSerializer(data=request.data)
        if serializer.is_valid():
            # Use the serializer to create and save the mongoengine Document
            product = serializer.save()
            return Response(ProductSerializer(product).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, pk=None):
        """
        Update an existing product.

        Retrieves a Product document by ObjectId, deserializes the incoming data,
        updates the document, and returns the serialized updated product.

        Args:
            request: The incoming request object containing updated product data.
            pk: The ObjectId string of the product to update.
        """
        try:
            # Retrieve the product by its ObjectId
            product = Product.objects.get(id=ObjectId(pk))
            serializer = ProductSerializer(product, data=request.data)
            if serializer.is_valid():
                # Use the serializer to update and save the mongoengine Document
                product = serializer.save()
                return Response(ProductSerializer(product).data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Product.DoesNotExist:
            # Return 404 if the product with the given ObjectId does not exist
            return Response(status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            # Handle other potential exceptions during ObjectId conversion or retrieval
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def destroy(self, request, pk=None):
        """
        Delete an existing product.

        Retrieves a Product document by ObjectId and deletes it from MongoDB.

        Args:
            request: The incoming request object.
            pk: The ObjectId string of the product to delete.
        """
        try:
            # Retrieve and delete the product by its ObjectId
            product = Product.objects.get(id=ObjectId(pk))
            product.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Product.DoesNotExist:
            # Return 404 if the product with the given ObjectId does not exist
            return Response(status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            # Handle other potential exceptions during ObjectId conversion or deletion
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class CustomProductPagination(PageNumberPagination):
    page_size = 10  # Set your desired page size here

ProductViewSet.pagination_class = CustomProductPagination