from rest_framework.mixins import RetrieveModelMixin, ListModelMixin
from rest_framework.viewsets import GenericViewSet
from shuup.core.models import PaymentMethod

from ._serializers import PaymentMethodSerializer
from ..mixins import ShopAPIViewSetMixin


class PaymentMethodViewSet(GenericViewSet, ShopAPIViewSetMixin, ListModelMixin):
    lookup_field = 'identifier'
    serializer_class = PaymentMethodSerializer

    def get_queryset(self, *args, **kwargs):
        return PaymentMethod.objects.filter(shop=self.get_shop(), enabled=True)
