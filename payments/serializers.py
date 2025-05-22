from rest_framework import serializers
from discounts.documents import Discount

class DiscountSerializer(DocumentSerializer):
    class Meta:
        document = Discount
        fields = '__all__'