from django.conf.urls import url, include
from rest_framework_extensions.routers import ExtendedSimpleRouter

from .api.basket import APIBasketLineViewSet
from .api.basket import APIBasketViewSet
from .api.shop import PublicShopViewSet

router = ExtendedSimpleRouter()
shop_router = router.register('shop', PublicShopViewSet, base_name='shop')
basket_router = shop_router.register(r'basket', APIBasketViewSet, base_name='basket', parents_query_lookups=['shop__identifier'])
basket_router.register(r'line', APIBasketLineViewSet, base_name='basket_line', parents_query_lookups=['shop__identifier', 'basket__key'])

urlpatterns = [
    url(r'^public/', include(router.urls))
]
