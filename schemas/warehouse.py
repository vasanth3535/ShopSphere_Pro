from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator


class WarehouseCreate(BaseModel):
    name: str = Field(min_length=2, max_length=150)
    code: str = Field(min_length=2, max_length=50, pattern=r"^[A-Z0-9_-]+$")
    address: str = Field(min_length=5)
    city: str = Field(min_length=2, max_length=100)
    state: str = Field(min_length=2, max_length=100)
    country: str = Field(min_length=2, max_length=100)
    capacity: int = Field(gt=0)


class WarehouseUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=150)
    address: str | None = Field(default=None, min_length=5)
    city: str | None = Field(default=None, min_length=2, max_length=100)
    state: str | None = Field(default=None, min_length=2, max_length=100)
    country: str | None = Field(default=None, min_length=2, max_length=100)
    capacity: int | None = Field(default=None, gt=0)
    is_active: bool | None = None


class WarehouseResponse(BaseModel):
    id: int
    name: str
    code: str
    address: str
    city: str
    state: str
    country: str
    capacity: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class WarehouseInventoryCreate(BaseModel):
    inventory_id: int = Field(gt=0)
    initial_quantity: int = Field(default=0, ge=0)


class WarehouseInventoryResponse(BaseModel):
    id: int
    warehouse_id: int
    inventory_id: int
    total_quantity: int
    reserved_quantity: int
    available_quantity: int
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class WarehouseCapacityResponse(BaseModel):
    warehouse_id: int
    capacity: int
    occupied_quantity: int
    available_capacity: int
    utilization_percentage: float
