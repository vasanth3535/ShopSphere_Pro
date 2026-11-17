from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from database.connection import get_db
from schemas.inventory import (
    InventoryCreate,
    InventoryAdjustment,
    InventoryReservation,
    InventoryResponse,
    InventoryMovementResponse
)
from services.inventory_service import (
    create_inventory,
    adjust_inventory,
    reserve_inventory,
    release_inventory,
    list_inventory,
    get_inventory,
    get_inventory_movements
)
from utils.dependencies import get_current_user
from utils.permissions import require_roles


router = APIRouter(
    prefix="/inventory",
    tags=["MODULE 13 - Inventory Management"]
)

inventory_roles = [
    "SUPER_ADMIN",
    "ADMIN",
    "INVENTORY_MANAGER"
]


@router.post(
    "/",
    response_model=InventoryResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_roles(*inventory_roles))]
)
def add_inventory(
    data: InventoryCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    return create_inventory(db, data, current_user.id)


@router.get(
    "/",
    response_model=list[InventoryResponse],
    dependencies=[Depends(require_roles(*inventory_roles))]
)
def get_inventory_records(
    product_id: int | None = Query(None, gt=0),
    db: Session = Depends(get_db)
):
    return list_inventory(db, product_id)


@router.get(
    "/{inventory_id}",
    response_model=InventoryResponse,
    dependencies=[Depends(require_roles(*inventory_roles))]
)
def get_inventory_record(
    inventory_id: int,
    db: Session = Depends(get_db)
):
    return get_inventory(db, inventory_id)


@router.post(
    "/{inventory_id}/adjust",
    response_model=InventoryResponse,
    dependencies=[Depends(require_roles(*inventory_roles))]
)
def update_stock(
    inventory_id: int,
    data: InventoryAdjustment,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    return adjust_inventory(db, inventory_id, data, current_user.id)


@router.post(
    "/{inventory_id}/reserve",
    response_model=InventoryResponse,
    dependencies=[Depends(require_roles(*inventory_roles))]
)
def reserve_stock(
    inventory_id: int,
    data: InventoryReservation,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    return reserve_inventory(
        db,
        inventory_id,
        data.quantity,
        current_user.id
    )


@router.post(
    "/{inventory_id}/release",
    response_model=InventoryResponse,
    dependencies=[Depends(require_roles(*inventory_roles))]
)
def release_reserved_stock(
    inventory_id: int,
    data: InventoryReservation,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    return release_inventory(
        db,
        inventory_id,
        data.quantity,
        current_user.id
    )


@router.get(
    "/{inventory_id}/movements",
    response_model=list[InventoryMovementResponse],
    dependencies=[Depends(require_roles(*inventory_roles))]
)
def get_inventory_movement_history(
    inventory_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    return get_inventory_movements(db, inventory_id, page, page_size)
