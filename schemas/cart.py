from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class CartItemCreate(BaseModel):
    product_id: int = Field(gt=0)
    variant_id: int | None = Field(default=None, gt=0)
    quantity: int = Field(gt=0)


class CartItemUpdate(BaseModel):
    quantity: int = Field(gt=0)


class CartItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    product_id: int
    variant_id: int | None
    quantity: int
    unit_price: Decimal
    created_at: datetime
    updated_at: datetime


class ShoppingCartResponse(BaseModel):
    id: int
    customer_id: int
    status: str
    items: list[CartItemResponse]
    subtotal: Decimal
    total_items: int
    created_at: datetime
    updated_at: datetime
