from decimal import Decimal

from pydantic import BaseModel, Field


class CartPriceCalculationRequest(BaseModel):
    coupon_code: str | None = Field(default=None, max_length=50)


class CartPriceCalculationResponse(BaseModel):
    cart_id: int
    subtotal: Decimal
    discount_amount: Decimal
    shipping_amount: Decimal
    taxable_amount: Decimal
    tax_percentage: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    total_items: int
    coupon_code: str | None
