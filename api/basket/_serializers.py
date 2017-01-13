from rest_framework.relations import PrimaryKeyRelatedField
from shuup.core.api.orders import AddressSerializer
from rest_framework import serializers
from rest_framework.fields import SerializerMethodField
from shuup.core.models import Product, OrderLineType, Shop, PaymentMethod
from shuup.core.pricing import PricingContext

from ..tax import ExtendedTaxClassSerializer
from ..products import PublicProductSerializer




class APIBasketLineSerializer(serializers.Serializer):
    product = PublicProductSerializer()
    base_unit_price = serializers.DecimalField(decimal_places=2, max_digits=500)
    discount_amount = serializers.DecimalField(decimal_places=2, max_digits=500)
    net_weight = serializers.FloatField()
    gross_weight = serializers.FloatField()
    shipping_mode = serializers.CharField()
    sku = serializers.CharField()
    text = SerializerMethodField()
    quantity = serializers.FloatField()
    tax_class = ExtendedTaxClassSerializer()
    line_id = serializers.CharField()

    @staticmethod
    def get_text(obj):
        return obj.product.safe_translation_getter("name", any_language=True)


class APIBasketDiscountSerializer(serializers.Serializer):
    discount_amount = serializers.DecimalField(decimal_places=2, max_digits=500)
    text = serializers.CharField()


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
    discounts = serializers.SerializerMethodField()

    def get_lines(self, basket):
        for line in basket.get_lines():
            line.cache_info(PricingContext(basket.shop, basket.customer))
            serializer = APIBasketLineSerializer(line, context={'request': self.context['request']})
            yield serializer.data

    def get_discounts(self, basket):
        for line in basket.get_final_lines():
            if line.type == OrderLineType.DISCOUNT:
                yield APIBasketDiscountSerializer(line).data


class CreateAPIBasketSerializer(serializers.Serializer):
    pass


class CouponAPIBasketSerializer(serializers.Serializer):
    code = serializers.CharField()


class CheckoutSerializer(serializers.Serializer):
    payment_method = PrimaryKeyRelatedField(queryset=PaymentMethod.objects.all())
    shipping_method = PrimaryKeyRelatedField(queryset=PaymentMethod.objects.all())
    shipping_address = AddressSerializer()
    billing_address = AddressSerializer()
