from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class LowStockThresholdCreate(BaseModel):
    inventory_id: int = Field(gt=0)
    minimum_quantity: int = Field(ge=0)


class LowStockThresholdUpdate(BaseModel):
    minimum_quantity: int | None = Field(default=None, ge=0)
    is_active: bool | None = None
    notes: str | None = Field(default=None, max_length=1000)


class LowStockThresholdResponse(BaseModel):
    id: int
    inventory_id: int
    minimum_quantity: int
    is_active: bool
    created_by: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class LowStockAlertResponse(BaseModel):
    id: int
    inventory_id: int
    threshold_id: int
    current_quantity: int
    minimum_quantity: int
    status: str
    message: str
    resolved_at: datetime | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class LowStockHistoryResponse(BaseModel):
    id: int
    threshold_id: int
    previous_quantity: int | None
    new_quantity: int
    notes: str | None
    changed_by: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class LowStockReportItem(BaseModel):
    inventory_id: int
    product_id: int
    variant_id: int | None
    total_quantity: int
    reserved_quantity: int
    available_quantity: int
    minimum_quantity: int
    shortage_quantity: int
