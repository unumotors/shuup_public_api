from django.conf.urls import url, include
from rest_framework_extensions.routers import ExtendedSimpleRouter

from .api.shipping_method import ShippingMethodViewSet
from .api.payment_method import PaymentMethodViewSet
from .api.basket import APIBasketLineViewSet, APIBasketViewSet
from .api.product import PublicShopProductViewSet
from .api.order import PublicOrderViewSet
from .api.shop import PublicShopViewSet

router = ExtendedSimpleRouter()
shop_router = router.register('shop', PublicShopViewSet, base_name='shop')

# shop route
shop_router.register(r'payment_method', PaymentMethodViewSet,
                     base_name='payment_method',
                     parents_query_lookups=['shop__identifier'])
shop_router.register(r'shipping_method', ShippingMethodViewSet,
                     base_name='shipping_method',
                     parents_query_lookups=['shop__identifier'])
shop_router.register(r'product', PublicShopProductViewSet,
                     base_name='product',
                     parents_query_lookups=['shop__identifier'])
shop_router.register(r'order', PublicOrderViewSet,
                     base_name='order',
                     parents_query_lookups=['shop__identifier'])
basket_router = shop_router.register(r'basket', APIBasketViewSet,
                                     base_name='basket',
                                     parents_query_lookups=['shop__identifier'])


# basket route
basket_router.register(r'line', APIBasketLineViewSet,
                       base_name='basket_line',
                       parents_query_lookups=['shop__identifier', 'basket__key'])

urlpatterns = [
    url(r'^public/', include(router.urls))
]
