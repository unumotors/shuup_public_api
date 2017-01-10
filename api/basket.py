from django.utils.translation import ugettext_lazy as _
from django_filters.rest_framework import DjangoFilterBackend, FilterSet
from rest_framework.serializers import ModelSerializer
from rest_framework.viewsets import ModelViewSet

from shuup.api.mixins import PermissionHelperMixin, ProtectedModelViewSetMixin
from shuup.front.models.stored_basket import StoredBasket


class StoredBasketSerializer(ModelSerializer):
    class Meta:
        fields = '__all__'
        model = StoredBasket


class StoredBasketFilter(FilterSet):
    class Meta:
        model = StoredBasket
        fields = ['shop']


class StoredBasketViewSet(ProtectedModelViewSetMixin, PermissionHelperMixin, ModelViewSet):
    queryset = StoredBasket.objects.all()
    serializer_class = StoredBasketSerializer
    filter_backends = (DjangoFilterBackend,)
    filter_class = StoredBasketFilter

    def get_view_name(self):
        return _('Baskets')

    @classmethod
    def get_help_text(cls):
        return _('Baskets can be listed, fetched, created, updated and deleted.')
