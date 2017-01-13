from django.http.response import Http404
from rest_framework.exceptions import ValidationError
from rest_framework_extensions.mixins import NestedViewSetMixin
from shuup.core.models import Shop
from shuup.front.basket.storage import ShopMismatchBasketCompatibilityError
from django.utils.translation import ugettext as _

from ..common.basket import APIBasket


class ShopAPIViewSetMixin(NestedViewSetMixin):
    def initialize_request(self, request, *args, **kwargs):
        request = super(ShopAPIViewSetMixin, self).initialize_request(request, *args, **kwargs)
        request.shop = self.get_shop()
        return request

    def get_shop(self):
        shop = Shop.objects.get(
            identifier=super(ShopAPIViewSetMixin, self).get_parents_query_dict()['shop__identifier']
        )
        return shop


class BasketAPIViewSetMixin(NestedViewSetMixin):
    def initialize_request(self, request, *args, **kwargs):
        request = super(BasketAPIViewSetMixin, self).initialize_request(request, *args, **kwargs)
        request.basket = self.get_basket()
        return request

    def get_basket(self, *args, **kwargs):
        try:
            basket_key = super(BasketAPIViewSetMixin, self).get_parents_query_dict()['basket__key']
        except KeyError:
            raise Exception('Couldn\'t find basket__key in parent query dict - '
                            'make sure this ViewSet is is a nested route of basket')
        basket = APIBasket(basket_key, self.get_shop())
        if not basket.is_stored:
            raise Http404
        try:
            APIBasket(super(BasketAPIViewSetMixin, self)
                      .get_parents_query_dict()['basket__key'], self.get_shop()).save()
        except ShopMismatchBasketCompatibilityError:
            raise ValidationError({
                'error': _('The requested belongs to another shop'),
                'code': 'shop_mismatch'
            }, 'shop_mismatch')
        return basket
