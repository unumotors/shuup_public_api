from shuup.core.api.category import CategorySerializer
from shuup.core.api.product_media import ProductMediaSerializer
from shuup.core.api.products import ProductAttributeSerializer, ProductPackageLinkSerializer
from rest_framework import serializers
from enumfields.fields import EnumField
from parler_rest.fields import TranslatedFieldsField
from parler_rest.serializers import TranslatableModelSerializer
from shuup.core.models import Product, ProductPackageLink, ShippingMode
from shuup.core.models import ShopProduct

from ..tax import ExtendedTaxClassSerializer


class PublicProductSerializer(TranslatableModelSerializer):
    sku = serializers.CharField()
    translations = TranslatedFieldsField(shared_model=Product)
    primary_image = ProductMediaSerializer(read_only=True)
    media = ProductMediaSerializer(read_only=True, many=True)
    shipping_mode = EnumField(enum=ShippingMode)
    attributes = ProductAttributeSerializer(many=True, read_only=True)
    package_content = serializers.SerializerMethodField()
    tax_class = ExtendedTaxClassSerializer()

    def get_package_content(self, product):
        return ProductPackageLinkSerializer(ProductPackageLink.objects.filter(parent=product),
                                            many=True,
                                            context={'request': self.context['request']}).data

    class Meta:
        model = Product
        fields = [
            'id',
            'sku',
            'translations',
            'primary_image',
            'media',
            'shipping_mode',
            'attributes',
            'package_content',
            'tax_class'
        ]


class PublicShopProductSerializer(TranslatableModelSerializer):
    product = PublicProductSerializer()
    default_price = serializers.DecimalField(max_digits=500, decimal_places=2)
    primary_category = CategorySerializer()

    class Meta:
        model = ShopProduct
        fields = [
            'product',
            'default_price',
            'primary_category',
        ]
