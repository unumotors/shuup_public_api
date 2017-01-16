import uuid

from django.core.exceptions import ObjectDoesNotExist
from django.http.response import Http404
from django.utils.translation import ugettext as _
from rest_framework.decorators import detail_route
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet
from shuup.core.api.orders import OrderSerializer
from shuup.core.models import OrderStatus
from shuup.core.pricing import PricingContext
from shuup.front.basket import get_basket_order_creator
from shuup.front.basket.commands import handle_add, handle_del, handle_update, handle_add_campaign_code
from shuup.front.basket.storage import ShopMismatchBasketCompatibilityError

from . import APIBasketSerializer, APIBasketLineSerializer, \
    CreateAPIBasketLineSerializer, ModifyAPIBasketLineSerializer, \
    DestroyAPIBasketLineSerializer, CouponAPIBasketSerializer, \
    CreateAPIBasketSerializer, CheckoutSerializer

from ..mixins import ShopAPIViewSetMixin, BasketAPIViewSetMixin
from ...common.basket import APIBasket


class APIBasketViewSet(GenericViewSet, ShopAPIViewSetMixin):
    lookup_field = 'key'
    permission_classes = [AllowAny]

    def get_serializer_class(self):
        return {
            'retrieve': APIBasketSerializer,
            'create': CreateAPIBasketSerializer,
            'add_discount': CouponAPIBasketSerializer,
            'remove_discount': CouponAPIBasketSerializer,
            'checkout': CheckoutSerializer
        }[self.action]

    def get_basket(self, *args, **kwargs):
        basket = APIBasket(self.kwargs['key'], self.get_shop())
        if not basket.is_stored or not basket.is_active:
            raise Http404
        try:
            basket.storage.load(basket)
        except ShopMismatchBasketCompatibilityError:
            raise ValidationError({
                'error': _('The requested belongs to another shop'),
                'code': 'shop_mismatch'
            }, 'shop_mismatch')
        return basket

    def retrieve(self, request, *args, **kwargs):
        basket = self.get_basket()
        return Response(self.get_serializer_class()(basket, context={'request': request}).data)

    def create(self, request, *args, **kwargs):
        shop = self.get_shop()
        basket = APIBasket(uuid.uuid4().hex, shop)
        basket.save()
        return Response(APIBasketSerializer(basket, context={'request': request}).data)

    @detail_route(methods=['post'])
    def add_discount(self, request, *args, **kwargs):
        basket = self.get_basket()
        serializer = self.get_serializer_class()(data=request.data)
        if serializer.is_valid(raise_exception=True):
            result = handle_add_campaign_code(request, basket, serializer.validated_data['code'])
            if not result['ok']:
                raise ValidationError({
                    'error': _('The entered code couldn\'t be applied to the basket'),
                    'code': 'invalid_code'
                }, 'invalid_code')
            basket.save()
            new_basket = self.get_basket()
            return Response(APIBasketSerializer(new_basket, context={'request': request}).data)

    @detail_route(methods=['post'])
    def remove_discount(self, request, *args, **kwargs):
        basket = self.get_basket()
        serializer = self.get_serializer_class()(data=request.data)
        if serializer.is_valid(raise_exception=True):
            basket.remove_code(serializer.validated_data['code'])
            basket.save()
            new_basket = self.get_basket()
            return Response(APIBasketSerializer(new_basket, context={'request': request}).data)

    @detail_route(methods=['post'])
    def checkout(self, request, *args, **kwargs):
        serializer = CheckoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        basket = self.get_basket()
        basket.verify_orderability()
        basket.shipping_method = serializer.validated_data['shipping_method']
        basket.payment_method = serializer.validated_data['payment_method']
        if basket.product_count < 1:
            raise ValidationError({
                'code': 'empty_basket',
                'error': 'You can\'t order an empty basket'
            })
        basket.status = OrderStatus.objects.get_default_initial()
        order_creator = get_basket_order_creator()
        order = order_creator.create_order(basket)
        basket.finalize()
        basket.save()

        return Response(OrderSerializer(order).data)


class APIBasketLineViewSet(GenericViewSet, ShopAPIViewSetMixin, BasketAPIViewSetMixin):
    lookup_field = 'line_id'
    permission_classes = [AllowAny]

    def get_serializer_class(self):
        return {
            'list': APIBasketLineSerializer,
            'create': CreateAPIBasketLineSerializer,
            'partial_update': ModifyAPIBasketLineSerializer,
            'destroy': DestroyAPIBasketLineSerializer
        }[self.action]

    def initialize_request(self, request, *args, **kwargs):
        request = super(APIBasketLineViewSet, self).initialize_request(request, *args, **kwargs)
        request.shop = self.get_shop()
        request.basket = self.get_basket()
        return request

    def create(self, request, *args, **kwargs):
        basket = self.get_basket()
        serializer = self.get_serializer_class()(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            product = serializer.validated_data['product']
            product.get_shop_instance(shop=self.request.shop)
        except ObjectDoesNotExist:
            return ValidationError({
                'code': 'product_not_available',
                'error': [_('The requested product does not exists or is not available in the current store')]
            })
        try:
            handle_add(PricingContext(self.request.shop, basket.customer),
                       basket, product.id, serializer.validated_data['quantity'])
            basket.save()
        except ShopMismatchBasketCompatibilityError:
            raise ValidationError({
                'code': 'shop_mismatch',
                'error': _('The requested belongs to another shop')
            })

        # trigger reload, otherwise we have a cached version
        new_basket = self.get_basket()
        return Response(APIBasketSerializer(new_basket, context={'request': self.request}).data)

    def partial_update(self, request, *args, **kwargs):
        serializer = self.get_serializer_class()(data=request.data)
        if serializer.is_valid(raise_exception=True):
            # super weird, sorry for that - it's the implementation of their basket thing
            update_command = 'q_{}'.format(kwargs['line_id'])
            update_args = {
                update_command: serializer.validated_data['quantity']
            }
            handle_update(request, request.basket, **update_args)
            request.basket.save()
            new_basket = self.get_basket()
            return Response(APIBasketSerializer(new_basket, context={'request': self.request}).data)

    def destroy(self, request, *args, **kwargs):
        result = handle_del(self.request, self.request.basket, kwargs['line_id'])
        if not result['ok']:
            raise ValidationError({
                'code': 'line_not_found',
                'error': _('Couldn\'t delete the line')
            })
        self.request.basket.save()
        new_basket = self.get_basket()
        return Response(APIBasketSerializer(new_basket, context={'request': self.request}).data)
