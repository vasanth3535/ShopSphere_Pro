from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class InventoryTransferCreate(BaseModel):
    source_warehouse_id: int = Field(gt=0)
    destination_warehouse_id: int = Field(gt=0)
    inventory_id: int = Field(gt=0)
    requested_quantity: int = Field(gt=0)
    notes: str | None = Field(default=None, max_length=1000)

    @model_validator(mode="after")
    def validate_warehouses(self):
        if self.source_warehouse_id == self.destination_warehouse_id:
            raise ValueError(
                "Source and destination warehouses must be different"
            )
        return self


class InventoryTransferDispatch(BaseModel):
    dispatched_quantity: int = Field(gt=0)
    notes: str | None = Field(default=None, max_length=1000)


class InventoryTransferReceive(BaseModel):
    received_quantity: int = Field(gt=0)
    notes: str | None = Field(default=None, max_length=1000)


class InventoryTransferCancel(BaseModel):
    notes: str = Field(min_length=3, max_length=1000)


class InventoryTransferResponse(BaseModel):
    id: int
    transfer_code: str
    source_warehouse_id: int
    destination_warehouse_id: int
    inventory_id: int
    requested_quantity: int
    dispatched_quantity: int
    received_quantity: int
    status: str
    notes: str | None
    requested_by: int
    dispatched_by: int | None
    received_by: int | None
    requested_at: datetime
    dispatched_at: datetime | None
    received_at: datetime | None
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class InventoryTransferHistoryResponse(BaseModel):
    id: int
    transfer_id: int
    previous_status: str | None
    new_status: str
    quantity: int
    notes: str | None
    performed_by: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class InventoryTransferStatusFilter(BaseModel):
    status: Literal[
        "REQUESTED",
        "DISPATCHED",
        "PARTIALLY_RECEIVED",
        "RECEIVED",
        "CANCELLED"
    ]
