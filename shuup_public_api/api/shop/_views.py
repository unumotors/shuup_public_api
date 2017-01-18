from django.utils.translation import ugettext_lazy as _
from rest_framework.mixins import RetrieveModelMixin
from rest_framework.permissions import AllowAny
from rest_framework.viewsets import GenericViewSet
from shuup.core.models import Shop

from ._serializers import PublicShopSerializer


class PublicShopViewSet(RetrieveModelMixin, GenericViewSet):
    serializer_class = PublicShopSerializer
    queryset = Shop.objects.all()
    permission_classes = [AllowAny]
    lookup_field = 'identifier'
    lookup_url_kwarg = 'identifier'

    def get_view_name(self):
        return _('Shops')

    def retrieve(self, request, *args, **kwargs):
        raise Exception('Boom bam')
