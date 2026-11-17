from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from database.connection import get_db
from models.user import User
from schemas.warehouse import (
    WarehouseCreate,
    WarehouseUpdate,
    WarehouseResponse,
    WarehouseInventoryCreate,
    WarehouseInventoryResponse,
    WarehouseCapacityResponse
)
from services import warehouse_service
from utils.dependencies import get_current_user
from utils.permissions import require_roles


router = APIRouter(
    prefix="/warehouses",
    tags=["MODULE 14 - Warehouse Management"]
)

warehouse_access = require_roles(
    "SUPER_ADMIN",
    "ADMIN",
    "INVENTORY_MANAGER"
)


@router.post(
    "/",
    response_model=WarehouseResponse,
    status_code=status.HTTP_201_CREATED
)
def create_warehouse(
    data: WarehouseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(warehouse_access)
):
    return warehouse_service.create_warehouse(db, data)


@router.get("/", response_model=list[WarehouseResponse])
def list_warehouses(
    active_only: bool = Query(default=False),
    db: Session = Depends(get_db),
    current_user: User = Depends(warehouse_access)
):
    return warehouse_service.list_warehouses(db, active_only)


@router.get(
    "/{warehouse_id}/inventory",
    response_model=list[WarehouseInventoryResponse]
)
def get_warehouse_inventory(
    warehouse_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(warehouse_access)
):
    return warehouse_service.get_warehouse_inventory(db, warehouse_id)


@router.get(
    "/{warehouse_id}/capacity",
    response_model=WarehouseCapacityResponse
)
def get_warehouse_capacity(
    warehouse_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(warehouse_access)
):
    return warehouse_service.get_warehouse_capacity(db, warehouse_id)


@router.post(
    "/{warehouse_id}/inventory",
    response_model=WarehouseInventoryResponse,
    status_code=status.HTTP_201_CREATED
)
def assign_inventory(
    warehouse_id: int,
    data: WarehouseInventoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(warehouse_access)
):
    return warehouse_service.assign_inventory(db, warehouse_id, data)


@router.get("/{warehouse_id}", response_model=WarehouseResponse)
def get_warehouse(
    warehouse_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(warehouse_access)
):
    return warehouse_service.get_warehouse(db, warehouse_id)


@router.patch("/{warehouse_id}", response_model=WarehouseResponse)
def update_warehouse(
    warehouse_id: int,
    data: WarehouseUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(warehouse_access)
):
    return warehouse_service.update_warehouse(db, warehouse_id, data)


@router.delete("/{warehouse_id}", response_model=WarehouseResponse)
def deactivate_warehouse(
    warehouse_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(warehouse_access)
):
    return warehouse_service.deactivate_warehouse(db, warehouse_id)
