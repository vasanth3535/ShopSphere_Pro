from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ProductPricingCreate(BaseModel):
    product_id: int = Field(gt=0)
    base_price: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    sale_price: Decimal | None = Field(default=None, ge=0, max_digits=12, decimal_places=2)
    valid_from: datetime
    valid_until: datetime | None = None
    change_reason: str | None = Field(default=None, max_length=500)

    @model_validator(mode="after")
    def validate_pricing(self):
        if self.sale_price is not None and self.sale_price >= self.base_price:
            raise ValueError("Sale price must be lower than base price")

        if self.valid_until is not None and self.valid_until <= self.valid_from:
            raise ValueError("valid_until must be later than valid_from")

        return self


class ProductPricingUpdate(BaseModel):
    base_price: Decimal | None = Field(default=None, gt=0, max_digits=12, decimal_places=2)
    sale_price: Decimal | None = Field(default=None, ge=0, max_digits=12, decimal_places=2)
    valid_from: datetime | None = None
    valid_until: datetime | None = None
    is_active: bool | None = None
    change_reason: str | None = Field(default=None, max_length=500)

    @model_validator(mode="after")
    def validate_pricing(self):
        if self.base_price is not None and self.sale_price is not None:
            if self.sale_price >= self.base_price:
                raise ValueError("Sale price must be lower than base price")

        if self.valid_from is not None and self.valid_until is not None:
            if self.valid_until <= self.valid_from:
                raise ValueError("valid_until must be later than valid_from")

        return self


class ProductPricingResponse(BaseModel):
    id: int
    product_id: int
    base_price: Decimal
    sale_price: Decimal | None
    valid_from: datetime
    valid_until: datetime | None
    is_active: bool
    created_by: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProductPriceHistoryResponse(BaseModel):
    id: int
    product_id: int
    pricing_id: int | None
    previous_base_price: Decimal | None
    new_base_price: Decimal
    previous_sale_price: Decimal | None
    new_sale_price: Decimal | None
    change_reason: str | None
    changed_by: int
    changed_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProductCurrentPriceResponse(BaseModel):
    product_id: int
    base_price: Decimal
    sale_price: Decimal | None
    effective_price: Decimal
    pricing_source: Literal["SCHEDULED", "PRODUCT_BASE_PRICE"]
    valid_from: datetime | None
    valid_until: datetime | None
