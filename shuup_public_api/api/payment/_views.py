from django.conf import settings

from rest_framework.mixins import ListModelMixin, RetrieveModelMixin
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet
from shuup.core.models import Payment
from shuup.core.api.orders import PaymentSerializer
from shuup.front.views.payment import get_payment_urls
from shuup.utils.http import retry_request


from ._serializers import CreateOrderPaymentSerializer, TransactionSerializer
from ..mixins import ShopAPIViewSetMixin, OrderAPIViewSetMixin


class OrderPaymentViewSet(GenericViewSet,
                          ShopAPIViewSetMixin,
                          OrderAPIViewSetMixin,
                          RetrieveModelMixin,
                          ListModelMixin):
    lookup_field = 'identifier'
    serializer_class = CreateOrderPaymentSerializer
    permission_classes = [AllowAny]

    def get_serializer_class(self, *args, **kwargs):
        return {
            'create': CreateOrderPaymentSerializer,
            'retrieve': PaymentSerializer,
            'list': PaymentSerializer,
        }[self.action]

    def get_queryset(self, *args, **kwargs):
        return Payment.objects.filter(order=self.get_order())

    def create(self, *args, **kwargs):
        serializer = self.get_serializer_class()(data=self.request.data)
        if serializer.is_valid(raise_exception=True):
            order = self.get_order()
            transaction_redirect = order.payment_method.get_payment_process_response(
                order=order,
                urls=get_payment_urls(request=self.request, order=order)
            )
            return Response(TransactionSerializer({
                'payment_url': transaction_redirect.url
            }).data)
