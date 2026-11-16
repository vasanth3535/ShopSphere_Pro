from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class ProductVariantCreate(BaseModel):
    product_id: int = Field(gt=0)
    sku: str = Field(min_length=2, max_length=100)
    variant_name: str = Field(min_length=2, max_length=150)
    attributes: str | None = Field(default=None, max_length=1000)
    price_adjustment: Decimal = Field(default=Decimal("0.00"), max_digits=12, decimal_places=2)
    stock_quantity: int = Field(default=0, ge=0)
    is_active: bool = True


class ProductVariantUpdate(BaseModel):
    sku: str | None = Field(default=None, min_length=2, max_length=100)
    variant_name: str | None = Field(default=None, min_length=2, max_length=150)
    attributes: str | None = Field(default=None, max_length=1000)
    price_adjustment: Decimal | None = Field(default=None, max_digits=12, decimal_places=2)
    stock_quantity: int | None = Field(default=None, ge=0)
    is_active: bool | None = None


class ProductVariantResponse(BaseModel):
    id: int
    product_id: int
    sku: str
    variant_name: str
    attributes: str | None
    price_adjustment: Decimal
    stock_quantity: int
    is_active: bool

    model_config = ConfigDict(from_attributes=True)
