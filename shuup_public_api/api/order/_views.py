from rest_framework.mixins import RetrieveModelMixin
from rest_framework.permissions import AllowAny
from rest_framework.viewsets import GenericViewSet
from shuup.core.models import Order

from ._serializers import OrderSerializer
from ..mixins import ShopAPIViewSetMixin


class PublicOrderViewSet(GenericViewSet, ShopAPIViewSetMixin, RetrieveModelMixin):
    serializer_class = OrderSerializer
    permission_classes = [AllowAny]
    lookup_field = 'key'

    def get_queryset(self, *args, **kwargs):
        return Order.objects.filter(shop=self.get_shop())
