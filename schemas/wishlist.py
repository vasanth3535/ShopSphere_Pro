from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class WishlistCreate(BaseModel):
    product_id: int


class WishlistItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    product_id: int
    created_at: datetime


class WishlistProductResponse(BaseModel):
    wishlist_id: int
    product_id: int
    product_name: str
    sku: str
    base_price: Decimal
    is_available: bool
    created_at: datetime


class WishlistResponse(BaseModel):
    customer_id: int
    total_items: int
    items: list[WishlistProductResponse]
