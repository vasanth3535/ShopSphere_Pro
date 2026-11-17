from typing import Literal

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from database.connection import get_db
from schemas.inventory_transfer import (
    InventoryTransferCreate,
    InventoryTransferDispatch,
    InventoryTransferReceive,
    InventoryTransferCancel,
    InventoryTransferResponse,
    InventoryTransferHistoryResponse
)
from services import inventory_transfer_service
from utils.dependencies import get_current_user
from utils.permissions import require_roles


router = APIRouter(
    prefix="/inventory-transfers",
    tags=["MODULE 15 - Inventory Transfers"]
)

transfer_access = require_roles(
    "SUPER_ADMIN",
    "ADMIN",
    "INVENTORY_MANAGER"
)


@router.post(
    "/",
    response_model=InventoryTransferResponse,
    status_code=status.HTTP_201_CREATED
)
def create_transfer(
    data: InventoryTransferCreate,
    db: Session = Depends(get_db),
    current_user=Depends(transfer_access)
):
    return inventory_transfer_service.create_transfer(
        db, data, current_user.id
    )


@router.get("/", response_model=list[InventoryTransferResponse])
def list_transfers(
    transfer_status: Literal[
        "REQUESTED",
        "DISPATCHED",
        "PARTIALLY_RECEIVED",
        "RECEIVED",
        "CANCELLED"
    ] | None = Query(default=None, alias="status"),
    warehouse_id: int | None = Query(default=None, gt=0),
    db: Session = Depends(get_db),
    current_user=Depends(transfer_access)
):
    return inventory_transfer_service.list_transfers(
        db, transfer_status, warehouse_id
    )


@router.post(
    "/{transfer_id}/dispatch",
    response_model=InventoryTransferResponse
)
def dispatch_transfer(
    transfer_id: int,
    data: InventoryTransferDispatch,
    db: Session = Depends(get_db),
    current_user=Depends(transfer_access)
):
    return inventory_transfer_service.dispatch_transfer(
        db, transfer_id, data, current_user.id
    )


@router.post(
    "/{transfer_id}/receive",
    response_model=InventoryTransferResponse
)
def receive_transfer(
    transfer_id: int,
    data: InventoryTransferReceive,
    db: Session = Depends(get_db),
    current_user=Depends(transfer_access)
):
    return inventory_transfer_service.receive_transfer(
        db, transfer_id, data, current_user.id
    )


@router.post(
    "/{transfer_id}/cancel",
    response_model=InventoryTransferResponse
)
def cancel_transfer(
    transfer_id: int,
    data: InventoryTransferCancel,
    db: Session = Depends(get_db),
    current_user=Depends(transfer_access)
):
    return inventory_transfer_service.cancel_transfer(
        db, transfer_id, data, current_user.id
    )


@router.get(
    "/{transfer_id}/history",
    response_model=list[InventoryTransferHistoryResponse]
)
def get_transfer_history(
    transfer_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(transfer_access)
):
    return inventory_transfer_service.get_transfer_history(
        db, transfer_id
    )


@router.get("/{transfer_id}", response_model=InventoryTransferResponse)
def get_transfer(
    transfer_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(transfer_access)
):
    return inventory_transfer_service.get_transfer(db, transfer_id)
