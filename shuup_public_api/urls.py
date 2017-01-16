from django.conf.urls import url, include
from rest_framework_extensions.routers import ExtendedSimpleRouter

from .api.shipping_method import ShippingMethodViewSet
from .api.payment_method import PaymentMethodViewSet
from .api.basket import APIBasketLineViewSet, APIBasketViewSet
from .api.product import PublicShopProductViewSet
from .api.order import PublicOrderViewSet
from .api.shop import PublicShopViewSet

router = ExtendedSimpleRouter()
shop_router = router.register('shops', PublicShopViewSet, base_name='shops')

# shop route
shop_router.register(r'payment_methods', PaymentMethodViewSet,
                     base_name='payment_methods',
                     parents_query_lookups=['shop__identifier'])
shop_router.register(r'shipping_methods', ShippingMethodViewSet,
                     base_name='shipping_methods',
                     parents_query_lookups=['shop__identifier'])
shop_router.register(r'products', PublicShopProductViewSet,
                     base_name='products',
                     parents_query_lookups=['shop__identifier'])
shop_router.register(r'orders', PublicOrderViewSet,
                     base_name='orders',
                     parents_query_lookups=['shop__identifier'])
basket_router = shop_router.register(r'baskets', APIBasketViewSet,
                                     base_name='baskets',
                                     parents_query_lookups=['shop__identifier'])


# basket route
basket_router.register(r'lines', APIBasketLineViewSet,
                       base_name='basket_lines',
                       parents_query_lookups=['shop__identifier', 'basket__key'])

urlpatterns = [
    url(r'^public/', include(router.urls))
]
