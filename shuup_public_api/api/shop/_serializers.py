from rest_framework.serializers import ModelSerializer
from shuup.core.models import Shop


class PublicShopSerializer(ModelSerializer):
    class Meta:
        fields = '__all__'
        model = Shop