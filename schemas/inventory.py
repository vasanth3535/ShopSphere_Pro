from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class InventoryCreate(BaseModel):
    product_id: int = Field(gt=0)
    variant_id: int | None = Field(default=None, gt=0)
    initial_quantity: int = Field(default=0, ge=0)


class InventoryAdjustment(BaseModel):
    movement_type: Literal["STOCK_IN", "STOCK_OUT"]
    quantity: int = Field(gt=0)
    reason: str = Field(min_length=3, max_length=500)
    reference: str | None = Field(default=None, max_length=100)


class InventoryReservation(BaseModel):
    quantity: int = Field(gt=0)


class InventoryResponse(BaseModel):
    id: int
    product_id: int
    variant_id: int | None
    total_quantity: int
    reserved_quantity: int
    available_quantity: int
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class InventoryMovementResponse(BaseModel):
    id: int
    inventory_id: int
    movement_type: str
    quantity: int
    previous_quantity: int
    new_quantity: int
    reason: str | None
    reference: str | None
    performed_by: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
