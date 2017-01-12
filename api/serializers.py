from shuup.core.api.product_media import ProductMediaSerializer
from shuup.core.api.products import ProductAttributeSerializer, ProductPackageLinkSerializer
from shuup.core.models import ShippingMode
from shuup.core.models import ProductPackageLink
from rest_framework import serializers
from enumfields.fields import EnumField
from parler_rest.fields import TranslatedFieldsField
from parler_rest.serializers import TranslatableModelSerializer
from rest_framework.fields import SerializerMethodField
from shuup.core.models import Product
from shuup.core.models import Shop
from shuup.core.pricing import PricingContext


class APIBasketLineProductSerializer(TranslatableModelSerializer):
    sku = serializers.CharField()
    translations = TranslatedFieldsField(shared_model=Product)
    primary_image = ProductMediaSerializer(read_only=True)
    media = ProductMediaSerializer(read_only=True, many=True)
    shipping_mode = EnumField(enum=ShippingMode)
    attributes = ProductAttributeSerializer(many=True, read_only=True)
    package_content = serializers.SerializerMethodField()

    def get_package_content(self, product):
        return ProductPackageLinkSerializer(ProductPackageLink.objects.filter(parent=product),
                                            many=True,
                                            context={'request': self.context['request']}).data

    class Meta:
        model = Product
        fields = [
            'sku',
            'translations',
            'primary_image',
            'media',
            'shipping_mode',
            'attributes',
            'package_content'
        ]


class APIBasketLineSerializer(serializers.Serializer):
    product = APIBasketLineProductSerializer()
    base_unit_price = serializers.DecimalField(decimal_places=2, max_digits=500)
    discount_amount = serializers.DecimalField(decimal_places=2, max_digits=500)
    net_weight = serializers.FloatField()
    gross_weight = serializers.FloatField()
    shipping_mode = serializers.CharField()
    sku = serializers.CharField()
    text = SerializerMethodField()
    quantity = serializers.FloatField()
    line_id = serializers.CharField()

    @staticmethod
    def get_text(obj):
        return obj.product.safe_translation_getter("name", any_language=True)


class CreateAPIBasketLineSerializer(serializers.Serializer):
    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all())
    quantity = serializers.IntegerField()


class ModifyAPIBasketLineSerializer(serializers.Serializer):
    quantity = serializers.IntegerField(required=False)


class DestroyAPIBasketLineSerializer(serializers.Serializer):
    pass


class APIBasketSerializer(serializers.Serializer):
    lines = SerializerMethodField()
    key = serializers.CharField()
    product_count = serializers.IntegerField()
    taxless_total_price = serializers.DecimalField(decimal_places=2, max_digits=500)
    taxful_total_price = serializers.DecimalField(decimal_places=2, max_digits=500)
    taxful_total_discount = serializers.DecimalField(decimal_places=2, max_digits=500)
    currency = serializers.CharField()
    shop = serializers.PrimaryKeyRelatedField(queryset=Shop.objects.all())
    basket_name = serializers.CharField()

    def get_lines(self, basket):
        for line in basket.get_lines():
            line.cache_info(PricingContext(basket.shop, basket.customer))
            serializer = APIBasketLineSerializer(line, context={'request': self.context['request']})
            yield serializer.data


class AddCouponAPIBasketSerializer(serializers.Serializer):
    code = serializers.CharField()
