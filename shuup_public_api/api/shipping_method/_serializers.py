from parler_rest.fields import TranslatedFieldsField
from parler_rest.serializers import TranslatableModelSerializer
from shuup.core.models import ShippingMethod


class ShippingMethodSerializer(TranslatableModelSerializer):
    translations = TranslatedFieldsField(shared_model=ShippingMethod)

    class Meta:
        fields = (
            'id',
            'identifier',
            'logo',
            'translations'
        )
        model = ShippingMethod
