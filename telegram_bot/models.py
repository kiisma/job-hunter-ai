from dataclasses import dataclass, field
from typing import List


@dataclass
class ProductInfo:
    url: str
    name: str
    price: float
    currency: str
    weight_kg: float
    shipping_to_portugal: float  # 0.0 if free or not applicable


@dataclass
class OrderItem:
    product: ProductInfo
    quantity: int = 1


@dataclass
class OrderSummary:
    items: List[OrderItem]
    total_product_cost: float    # sum of item prices (original)
    markup_amount: float         # 25% markup
    total_weight_kg: float       # total estimated weight
    russia_shipping: float       # 15 EUR/kg to Russia
    portugal_shipping: float     # delivery within Portugal (0 if free)
    grand_total: float           # everything combined
    currency: str = "EUR"
