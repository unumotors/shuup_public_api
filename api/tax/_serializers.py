from shuup.core.api.tax_class import TaxClassSerializer
from parler_rest.fields import TranslatedFieldsField
from parler_rest.serializers import TranslatableModelSerializer
from rest_framework import serializers
from shuup.core.models import Tax


class TaxSerializer(TranslatableModelSerializer):
    translations = TranslatedFieldsField()
    type = serializers.SerializerMethodField()
    rate = serializers.DecimalField(max_digits=500, decimal_places=2)
    amount = serializers.DecimalField(max_digits=500, decimal_places=2)

    def get_type(self, tax):
        return 'amount' if tax.amount else 'rate'

    class Meta:
        model = Tax
        fields = [
            'translations',
            'rate',
            'type',
            'amount'
        ]


class ExtendedTaxClassSerializer(TaxClassSerializer):
    rules = serializers.SerializerMethodField()

    def get_rules(self, tax_class):
        for rule in tax_class.taxrule_set.filter(enabled=True):
            yield TaxSerializer(rule.tax).data
