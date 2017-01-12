from django.utils.translation import ugettext_lazy as _
from rest_framework.mixins import RetrieveModelMixin
from rest_framework.serializers import ModelSerializer
from rest_framework.viewsets import GenericViewSet

from shuup.core.models import Shop


class PublicShopSerializer(ModelSerializer):
    class Meta:
        fields = '__all__'
        model = Shop


class PublicShopViewSet(RetrieveModelMixin, GenericViewSet):
    serializer_class = PublicShopSerializer
    queryset = Shop.objects.all()
    lookup_field = 'identifier'
    lookup_url_kwarg = 'identifier'

    def get_view_name(self):
        return _('Shops')
