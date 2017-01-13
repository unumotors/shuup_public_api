from parler_rest.fields import TranslatedFieldsField
from parler_rest.serializers import TranslatableModelSerializer
from shuup.core.models import PaymentMethod


class PaymentMethodSerializer(TranslatableModelSerializer):
    translations = TranslatedFieldsField(shared_model=PaymentMethod)

    class Meta:
        fields = (
            'id',
            'identifier',
            'logo',
            'translations'
        )
        model = PaymentMethod
