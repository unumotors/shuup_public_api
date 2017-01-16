from rest_framework import serializers


class CreateOrderPaymentSerializer(serializers.Serializer):
    return_url = serializers.URLField()


class TransactionSerializer(serializers.Serializer):
    payment_url = serializers.URLField()
