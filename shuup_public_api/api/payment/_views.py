from django.conf import settings
from rest_framework.reverse import reverse
from rest_framework.decorators import list_route

from rest_framework.mixins import ListModelMixin, RetrieveModelMixin
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.status import HTTP_500_INTERNAL_SERVER_ERROR
from rest_framework.viewsets import GenericViewSet
from shuup.core.models import Payment
from shuup.core.api.orders import PaymentSerializer
from shuup.core.models import PaymentUrls


from ._serializers import CreateOrderPaymentSerializer, TransactionSerializer
from ..mixins import ShopAPIViewSetMixin, OrderAPIViewSetMixin


class OrderPaymentViewSet(GenericViewSet,
                          ShopAPIViewSetMixin,
                          OrderAPIViewSetMixin,
                          RetrieveModelMixin,
                          ListModelMixin):
    lookup_field = 'identifier'
    permission_classes = [AllowAny]

    def get_serializer_class(self, *args, **kwargs):
        return {
            'create': CreateOrderPaymentSerializer,
            'retrieve': PaymentSerializer,
            'list': PaymentSerializer,
            'callback': PaymentSerializer,
            'cancel': PaymentSerializer,
        }[self.action]

    def _reverse_url(self, viewname):
        return reverse(viewname, kwargs={
           'parent_lookup_shop__identifier': self.get_shop().identifier,
           'parent_lookup_order__key': self.get_order().key
        })

    def get_queryset(self, *args, **kwargs):
        return Payment.objects.filter(order=self.get_order())

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer_class()(data=self.request.data)
        if serializer.is_valid(raise_exception=True):
            order = self.get_order()
            transaction_redirect = order.payment_method.get_payment_process_response(
                order=order,
                urls=PaymentUrls(
                    return_url=serializer.validated_data.get(
                        'return_url',
                        request.build_absolute_uri(self._reverse_url('public_api:payments-callback-list'))),
                    cancel_url=serializer.validated_data.get(
                        'cancel_url',
                        request.build_absolute_uri(self._reverse_url('public_api:payments-cancel-list'))),
                    payment_url=None
                )
            )
            return Response(TransactionSerializer({
                'payment_url': transaction_redirect.url
            }).data)

    @list_route(methods=['post'])
    def callback(self, request, *args, **kwargs):
        order = self.get_order()
        payment_method = order.payment_method
        payment_method.process_payment_return_request(order=order, request=request)
        return Response('ok')

    @list_route(methods=['post'])
    def cancel(self, request, *args, **kwargs):
        return Response('Server method not implemented', status=HTTP_500_INTERNAL_SERVER_ERROR)