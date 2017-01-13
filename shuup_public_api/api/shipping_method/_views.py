from rest_framework.mixins import ListModelMixin
from rest_framework.permissions import AllowAny
from rest_framework.viewsets import GenericViewSet
from shuup.core.models import ShippingMethod

from ._serializers import ShippingMethodSerializer
from ..mixins import ShopAPIViewSetMixin


class ShippingMethodViewSet(GenericViewSet, ShopAPIViewSetMixin, ListModelMixin):
    lookup_field = 'identifier'
    serializer_class = ShippingMethodSerializer
    permission_classes = [AllowAny]

    def get_queryset(self, *args, **kwargs):
        return ShippingMethod.objects.filter(shop=self.get_shop(), enabled=True)
