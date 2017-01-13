
from rest_framework.mixins import ListModelMixin, RetrieveModelMixin
from rest_framework.viewsets import GenericViewSet

from ..mixins import ShopAPIViewSetMixin
from ._serializers import PublicShopProductSerializer


class PublicShopProductViewSet(GenericViewSet, ListModelMixin, RetrieveModelMixin, ShopAPIViewSetMixin):
    serializer_class = PublicShopProductSerializer

    def get_queryset(self):
        return self.get_shop().shop_products.all()
