import uuid

import six
from collections import Counter

from decimal import Decimal
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _
from shuup.core.models import OrderLineType
from shuup.core.models import PaymentMethod
from shuup.core.models import ShippingMethod
from shuup.core.order_creator import OrderSource, SourceLine
from shuup.core.pricing import PricingContext
from shuup.core.utils.users import real_user_or_none
from shuup.front.basket.objects import BasketLine
from shuup.front.basket.storage import BasketStorage, ShopMismatchBasketCompatibilityError, _price_units_diff, \
    PriceUnitMismatchBasketCompatibilityError
from shuup.front.models.stored_basket import StoredBasket
from shuup.utils.numbers import parse_decimal_string
from shuup.utils.objects import compare_partial_dicts


class APIBasket(OrderSource):
    def __init__(self, key, shop, ip_address=None, customer=None, orderer=None, creator=None, basket_name="basket"):
        super(APIBasket, self).__init__(shop)
        self.basket_name = basket_name
        self.ip_address = ip_address
        self.storage = DatabaseAPIBasketStorage()
        self._data = None
        self.customer = customer
        self.orderer = orderer
        self.creator = creator
        self._orderable_lines_cache = None
        self._unorderable_lines_cache = None
        self._lines_cached = False
        self.key = key

    @property
    def is_stored(self):
        return self.storage.is_saved(self)

    def _load(self):
        """
        Get the currently persisted data for this basket.

        This will only access the storage once per request in usual
        circumstances.

        :return: Data dict.
        :rtype: dict
        """
        if self._data is None:
            self._data = self.storage.load(basket=self)
        return self._data

    def save(self):
        """
        Persist any changes made into the basket to storage.
        """
        self.clean_empty_lines()
        self.storage.save(basket=self, data=self._data)

    def delete(self):
        """
        Clear and delete the basket data.
        """
        self.storage.delete(basket=self)
        self._data = None

    def finalize(self):
        """
        Mark the basket as "completed" (i.e. an order is created/a conversion made).

        This will also clear the basket's data.
        """
        self.storage.finalize(basket=self)
        self._data = None

    def clear_all(self):
        """
        Clear all data for this basket.
        """
        self._data = {}

    @property
    def _data_lines(self):
        """
        Get the line data (list of dicts).

        If the list is edited, it must be re-assigned
        to ``self._data_lines`` to ensure the `dirty`
        flag gets set.

        :return: List of data dicts
        :rtype: list[dict]
        """
        return self._load().setdefault("lines", [])

    @_data_lines.setter
    def _data_lines(self, new_lines):
        """
        Set the line data (list of dicts).

        Note that this assignment must be made instead
        of editing `_data_lines` in-place to ensure
        the `dirty` bit gets set.

        :param new_lines: New list of lines.
        :type new_lines: list[dict]
        """
        self._load()["lines"] = new_lines

    def add_line(self, **kwargs):
        line = self.create_line(**kwargs)
        self._data_lines = self._data_lines + [line.to_dict()]
        return line

    def create_line(self, **kwargs):
        return BasketLine(source=self, **kwargs)

    @property
    def _codes(self):
        return self._load().setdefault("codes", [])

    @_codes.setter
    def _codes(self, value):
        if hasattr(self, "_data"):  # Check that we're initialized
            self._load()["codes"] = value

    def add_code(self, code):
        modified = super(APIBasket, self).add_code(code)
        return modified

    def clear_codes(self):
        modified = super(APIBasket, self).clear_codes()
        return modified

    def remove_code(self, code):
        modified = super(APIBasket, self).remove_code(code)
        return modified

    @property
    def is_empty(self):
        return not bool(self.get_lines())

    def _cache_lines(self):
        lines = [BasketLine.from_dict(self, line) for line in self._data_lines]
        orderable_counter = Counter()
        orderable_lines = []
        for line in lines:
            if line.type != OrderLineType.PRODUCT:
                orderable_lines.append(line)
            else:
                product = line.product
                quantity = line.quantity + orderable_counter[product.id]
                if line.shop_product.is_orderable(line.supplier, self.customer, quantity, allow_cache=False):
                    if product.is_package_parent():
                        quantity_map = product.get_package_child_to_quantity_map()
                        orderable = True
                        for child_product, child_quantity in six.iteritems(quantity_map):
                            sp = child_product.get_shop_instance(shop=self.shop)
                            in_basket_child_qty = orderable_counter[child_product.id]
                            total_child_qty = ((quantity * child_quantity) + in_basket_child_qty)
                            if not sp.is_orderable(
                                    line.supplier, self.customer, total_child_qty, allow_cache=False):
                                orderable = False
                                break
                        if orderable:
                            orderable_lines.append(line)
                            orderable_counter[product.id] += quantity
                            for child_product, child_quantity in six.iteritems(quantity_map):
                                orderable_counter[child_product.id] += child_quantity * line.quantity
                    else:
                        orderable_lines.append(line)
                        orderable_counter[product.id] += line.quantity
        self._orderable_lines_cache = orderable_lines
        self._unorderable_lines_cache = [line for line in lines if line not in orderable_lines]
        self._lines_cached = True

    def get_unorderable_lines(self):
        return self._unorderable_lines_cache

    def get_lines(self):
        if not self._lines_cached:
            self._cache_lines()
        return self._orderable_lines_cache

    @staticmethod
    def _initialize_product_line_data(product, supplier, shop, quantity=0):
        if product.variation_children.count():
            raise ValueError("Attempting to add variation parent to basket")

        return {
            "line_id": uuid.uuid4().int,
            "product": product,
            "supplier": supplier,
            "shop": shop,
            "quantity": parse_decimal_string(quantity),
        }

    def clean_empty_lines(self):
        new_lines = [l for l in self._data_lines if l["quantity"] > 0]
        if len(new_lines) != len(self._data_lines):
            self._data_lines = new_lines

    def _compare_line_for_addition(self, current_line_data, product, supplier, shop, extra):
        """
        Compare raw line data for coalescing.

        That is, figure out whether the given raw line data is similar enough to product_id
        and extra to coalesce quantity additions.

        This is nice to override in a project-specific basket class.

        :type current_line_data: dict
        :type product: int
        :type extra: dict
        :return:
        """
        if current_line_data.get("product_id") != product.id:
            return False
        if current_line_data.get("supplier_id") != supplier.id:
            return False
        if current_line_data.get("shop_id") != shop.id:
            return False

        if isinstance(extra, dict):  # We have extra data, so compare it to that in this line
            if not compare_partial_dicts(extra, current_line_data):  # Extra data not similar? Okay then. :(
                return False
        return True

    def _find_product_line_data(self, product, supplier, shop, extra):
        """
        Find the underlying basket data dict for a given product and line-specific extra data.
        This uses _compare_line_for_addition internally, which is nice to override in a project-specific basket class.

        :param product: Product object
        :param extra: optional dict of extra data
        :return: dict of line or None
        """
        for line_data in self._data_lines:
            if self._compare_line_for_addition(line_data, product, supplier, shop, extra):
                return line_data

    def _add_or_replace_line(self, data_line):
        if isinstance(data_line, SourceLine):
            data_line = data_line.to_dict()
        assert isinstance(data_line, dict)
        line_ids = [x["line_id"] for x in self._data_lines]
        try:
            index = line_ids.index(data_line["line_id"])
        except ValueError:
            index = len(line_ids)
        self.delete_line(data_line["line_id"])
        self._data_lines.insert(index, data_line)
        self._data_lines = list(self._data_lines)  # This will set the dirty bit and call uncache.

    def add_product(self, supplier, shop, product, quantity, force_new_line=False, extra=None, parent_line=None):
        if not extra:
            extra = {}

        if quantity <= 0:
            raise ValueError("Invalid quantity!")

        data = None
        if not force_new_line:
            data = self._find_product_line_data(product=product, supplier=supplier, shop=shop, extra=extra)

        if not data:
            data = self._initialize_product_line_data(product=product, supplier=supplier, shop=shop)

        if parent_line:
            data["parent_line_id"] = parent_line.line_id

        new_quantity = max(0, data["quantity"] + Decimal(quantity))

        return self.update_line(data, quantity=new_quantity, **extra)

    def update_line(self, data_line, **kwargs):
        line = BasketLine.from_dict(self, data_line)
        new_quantity = kwargs.pop("quantity", None)
        if new_quantity is not None:
            line.set_quantity(new_quantity)
        line.update(**kwargs)
        line.cache_info(PricingContext(self.shop, self.customer))
        self._add_or_replace_line(line)
        return line

    def add_product_with_child_product(self, supplier, shop, product, child_product, quantity):
        parent_line = self.add_product(
            supplier=supplier,
            shop=shop,
            product=product,
            quantity=quantity,
            force_new_line=True
        )
        child_line = self.add_product(
            supplier=supplier,
            shop=shop,
            product=child_product,
            quantity=quantity,
            parent_line=parent_line,
            force_new_line=True
        )
        return (parent_line, child_line)

    def delete_line(self, line_id):
        line = self.find_line_by_line_id(line_id)
        if line:
            line["quantity"] = 0
            for subline in self.find_lines_by_parent_line_id(line_id):
                subline["quantity"] = 0
            self.uncache()
            self.clean_empty_lines()
            return True
        return False

    def find_line_by_line_id(self, line_id):
        for line in self._data_lines:
            if six.text_type(line.get("line_id")) == six.text_type(line_id):
                return line
        return None

    def find_lines_by_parent_line_id(self, parent_line_id):
        for line in self._data_lines:
            if six.text_type(line.get("parent_line_id")) == six.text_type(parent_line_id):
                yield line

    def _get_orderable(self):
        return (sum(l.quantity for l in self.get_lines()) > 0)

    orderable = property(_get_orderable)

    def get_validation_errors(self):
        for error in super(APIBasket, self).get_validation_errors():
            yield error

        shipping_methods = self.get_available_shipping_methods()
        payment_methods = self.get_available_payment_methods()

        advice = _(
            "Try to remove some product from the basket "
            "and order them separately.")

        if self.has_shippable_lines() and not shipping_methods:
            msg = _("Products in basket cannot be shipped together. %s")
            yield ValidationError(msg % advice, code="no_common_shipping")

        if not payment_methods:
            msg = _("Products in basket have no common payment method. %s")
            yield ValidationError(msg % advice, code="no_common_payment")

    def get_product_ids_and_quantities(self):
        q_counter = Counter()
        for line in self.get_lines():
            if line.product:
                quantity_map = line.product.get_package_child_to_quantity_map()
                for child_product, child_quantity in six.iteritems(quantity_map):
                    q_counter[child_product.id] += line.quantity * child_quantity

                q_counter[line.product.id] += line.quantity
        return dict(q_counter)

    def get_available_shipping_methods(self):
        """
        Get available shipping methods.

        :rtype: list[ShippingMethod]
        """
        return [
            m for m
            in ShippingMethod.objects.available(shop=self.shop, products=self.product_ids)
            if m.is_available_for(self)
        ]

    def get_available_payment_methods(self):
        """
        Get available payment methods.

        :rtype: list[PaymentMethod]
        """
        return [
            m for m
            in PaymentMethod.objects.available(shop=self.shop, products=self.product_ids)
            if m.is_available_for(self)
        ]


class DatabaseAPIBasketStorage(BasketStorage):

    def is_saved(self, basket):
        return StoredBasket.objects.filter(key=basket.key).exists()

    def save(self, basket, data):
        """
        :type basket: shuup_public_api.models.APIBasket
        """
        stored_basket = self._get_stored_basket(basket)
        stored_basket.data = data
        stored_basket.taxless_total_price = basket.taxless_total_price_or_none
        stored_basket.taxful_total_price = basket.taxful_total_price_or_none
        stored_basket.product_count = basket.product_count
        stored_basket.customer = (basket.customer or None)
        stored_basket.orderer = (basket.orderer or None)
        stored_basket.creator = real_user_or_none(basket.creator)
        stored_basket.save()
        stored_basket.products = set(basket.product_ids)

    def load(self, basket):
        """
        Load the given basket's data dictionary from the storage.

        :type basket: shuup_public_api.api_basket.APIBasket
        :rtype: dict
        :raises:
          `BasketCompatibilityError` if basket loaded from the storage
          is not compatible with the requested basket.
        """
        stored_basket = self._load_stored_basket(basket)
        if not stored_basket:
            return {}
        if stored_basket.shop_id != basket.shop.id:
            msg = (
                "Cannot load basket of a different Shop ("
                "%s id=%r with Shop=%s, Dest. Basket Shop=%s)" % (
                    type(stored_basket).__name__,
                    stored_basket.id, stored_basket.shop_id, basket.shop.id))
            raise ShopMismatchBasketCompatibilityError(msg)
        price_unit_diff = _price_units_diff(stored_basket, basket.shop)
        if price_unit_diff:
            msg = "%s %r: Price unit mismatch with Shop (%s)" % (
                type(stored_basket).__name__, stored_basket.id,
                price_unit_diff)
            raise PriceUnitMismatchBasketCompatibilityError(msg)
        return stored_basket.data or {}

    def _load_stored_basket(self, basket):
        return self._get_stored_basket(basket)

    def delete(self, basket):
        stored_basket = self._get_stored_basket(basket)
        if stored_basket and stored_basket.pk:
            stored_basket.deleted = True
            stored_basket.save()

    def finalize(self, basket):
        stored_basket = self._get_stored_basket(basket)
        if stored_basket and stored_basket.pk:
            stored_basket.deleted = True
            stored_basket.finished = True
            stored_basket.save()

    @staticmethod
    def _get_stored_basket(basket):
        stored_basket = StoredBasket.objects.filter(deleted=False, key=basket.key)
        if stored_basket:
            stored_basket = stored_basket.first()
        if not stored_basket:
            stored_basket = StoredBasket(
                key=basket.key,
                shop=basket.shop,
                currency=basket.currency,
                prices_include_tax=basket.prices_include_tax,
            )
        return stored_basket
