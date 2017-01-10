from .basket import StoredBasketViewSet


def populate(router):
    router.register('shuup/cart', StoredBasketViewSet)
