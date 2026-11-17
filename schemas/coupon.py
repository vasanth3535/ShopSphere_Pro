from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class CouponCreate(BaseModel):
    code: str = Field(min_length=3, max_length=50)
    description: str | None = Field(default=None, max_length=255)
    discount_type: Literal["PERCENTAGE", "FIXED"]
    discount_value: Decimal = Field(gt=0, max_digits=10, decimal_places=2)
    minimum_purchase: Decimal = Field(default=Decimal("0.00"), ge=0, max_digits=10, decimal_places=2)
    valid_from: datetime
    valid_until: datetime
    is_active: bool = True

    @field_validator("code")
    @classmethod
    def normalize_code(cls, value: str) -> str:
        return value.strip().upper()

    @model_validator(mode="after")
    def validate_coupon(self):
        if self.valid_until <= self.valid_from:
            raise ValueError("Coupon end date must be after start date")

        if self.discount_type == "PERCENTAGE" and self.discount_value > 100:
            raise ValueError("Percentage discount cannot exceed 100")

        return self


class CouponUpdate(BaseModel):
    description: str | None = Field(default=None, max_length=255)
    discount_type: Literal["PERCENTAGE", "FIXED"] | None = None
    discount_value: Decimal | None = Field(default=None, gt=0, max_digits=10, decimal_places=2)
    minimum_purchase: Decimal | None = Field(default=None, ge=0, max_digits=10, decimal_places=2)
    valid_from: datetime | None = None
    valid_until: datetime | None = None

    @model_validator(mode="after")
    def validate_coupon(self):
        if (
            self.discount_type == "PERCENTAGE"
            and self.discount_value is not None
            and self.discount_value > 100
        ):
            raise ValueError("Percentage discount cannot exceed 100")

        if self.valid_from and self.valid_until and self.valid_until <= self.valid_from:
            raise ValueError("Coupon end date must be after start date")

        return self


class CouponStatusUpdate(BaseModel):
    is_active: bool


class CouponResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    description: str | None
    discount_type: str
    discount_value: Decimal
    minimum_purchase: Decimal
    valid_from: datetime
    valid_until: datetime
    is_active: bool
    created_at: datetime
    updated_at: datetime
