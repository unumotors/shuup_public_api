from rest_framework.serializers import ModelSerializer
from shuup.core.models import PaymentMethod


class PaymentMethodSerializer(ModelSerializer):
    class Meta:
        fields = (
            'identifier',
            'choice_identifier',
            'logo',
            'payment_processor'
        )
        model = PaymentMethod
