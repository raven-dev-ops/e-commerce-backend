from rest_framework_mongoengine.serializers import DocumentSerializer
from rest_framework import serializers

class PaymentSerializer(DocumentSerializer):
    class Meta:
        document = Payment
        fields = '__all__'