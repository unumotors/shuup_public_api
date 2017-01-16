from rest_framework import serializers


class CreateOrderPaymentSerializer(serializers.Serializer):
    return_url = serializers.URLField(required=False)
    cancel_url = serializers.URLField(required=False)
    payment_url = serializers.URLField(required=False)


class TransactionSerializer(serializers.Serializer):
    payment_url = serializers.URLField()
