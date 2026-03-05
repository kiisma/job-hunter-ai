from .models import OrderItem, OrderSummary
from .config import RUSSIA_SHIPPING_PER_KG, MARKUP_PERCENT


def calculate_order(items: list[OrderItem]) -> OrderSummary:
    total_product_cost = sum(i.product.price * i.quantity for i in items)
    markup_amount = round(total_product_cost * MARKUP_PERCENT / 100, 2)
    total_weight_kg = round(sum(i.product.weight_kg * i.quantity for i in items), 3)
    russia_shipping = round(total_weight_kg * RUSSIA_SHIPPING_PER_KG, 2)
    portugal_shipping = round(sum(i.product.shipping_to_portugal for i in items), 2)
    grand_total = round(
        total_product_cost + markup_amount + russia_shipping + portugal_shipping, 2
    )

    return OrderSummary(
        items=items,
        total_product_cost=round(total_product_cost, 2),
        markup_amount=markup_amount,
        total_weight_kg=total_weight_kg,
        russia_shipping=russia_shipping,
        portugal_shipping=portugal_shipping,
        grand_total=grand_total,
    )
