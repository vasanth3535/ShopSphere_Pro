from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from models.warehouse import Warehouse
from models.warehouse_inventory import WarehouseInventory
from models.inventory import Inventory
from schemas.warehouse import WarehouseCreate, WarehouseUpdate, WarehouseInventoryCreate


def get_warehouse_occupancy(db: Session, warehouse_id: int) -> int:
    return db.query(
        func.coalesce(func.sum(WarehouseInventory.total_quantity), 0)
    ).filter(
        WarehouseInventory.warehouse_id == warehouse_id
    ).scalar()


def create_warehouse(db: Session, data: WarehouseCreate):
    existing = db.query(Warehouse).filter(
        (Warehouse.name == data.name) | (Warehouse.code == data.code)
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Warehouse name or code already exists"
        )

    warehouse = Warehouse(**data.model_dump())
    db.add(warehouse)
    db.commit()
    db.refresh(warehouse)
    return warehouse


def list_warehouses(db: Session, active_only: bool = False):
    query = db.query(Warehouse)

    if active_only:
        query = query.filter(Warehouse.is_active.is_(True))

    return query.order_by(Warehouse.id.desc()).all()


def get_warehouse(db: Session, warehouse_id: int):
    warehouse = db.query(Warehouse).filter(
        Warehouse.id == warehouse_id
    ).first()

    if not warehouse:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Warehouse not found"
        )

    return warehouse


def update_warehouse(db: Session, warehouse_id: int, data: WarehouseUpdate):
    warehouse = get_warehouse(db, warehouse_id)
    updates = data.model_dump(exclude_unset=True)

    if "capacity" in updates and updates["capacity"] is not None:
        occupied = get_warehouse_occupancy(db, warehouse_id)

        if updates["capacity"] < occupied:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Warehouse capacity cannot be lower than occupied stock"
            )

    if "name" in updates and updates["name"] != warehouse.name:
        duplicate = db.query(Warehouse).filter(
            Warehouse.name == updates["name"],
            Warehouse.id != warehouse_id
        ).first()

        if duplicate:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Warehouse name already exists"
            )

    for field, value in updates.items():
        setattr(warehouse, field, value)

    db.commit()
    db.refresh(warehouse)
    return warehouse


def deactivate_warehouse(db: Session, warehouse_id: int):
    warehouse = get_warehouse(db, warehouse_id)
    warehouse.is_active = False
    db.commit()
    db.refresh(warehouse)
    return warehouse


def assign_inventory(
    db: Session,
    warehouse_id: int,
    data: WarehouseInventoryCreate
):
    warehouse = get_warehouse(db, warehouse_id)

    if not warehouse.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot assign inventory to an inactive warehouse"
        )

    inventory = db.query(Inventory).filter(
        Inventory.id == data.inventory_id
    ).first()

    if not inventory:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Inventory record not found"
        )

    existing = db.query(WarehouseInventory).filter(
        WarehouseInventory.warehouse_id == warehouse_id,
        WarehouseInventory.inventory_id == data.inventory_id
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Inventory is already assigned to this warehouse"
        )

    occupied = get_warehouse_occupancy(db, warehouse_id)
    remaining_capacity = warehouse.capacity - occupied

    if data.initial_quantity > remaining_capacity:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Insufficient warehouse capacity. Available capacity: {remaining_capacity}"
        )

    warehouse_inventory = WarehouseInventory(
        warehouse_id=warehouse_id,
        inventory_id=data.inventory_id,
        total_quantity=data.initial_quantity,
        reserved_quantity=0,
        available_quantity=data.initial_quantity
    )

    db.add(warehouse_inventory)
    db.commit()
    db.refresh(warehouse_inventory)
    return warehouse_inventory


def get_warehouse_inventory(db: Session, warehouse_id: int):
    get_warehouse(db, warehouse_id)

    return db.query(WarehouseInventory).filter(
        WarehouseInventory.warehouse_id == warehouse_id
    ).order_by(WarehouseInventory.id.desc()).all()


def get_warehouse_capacity(db: Session, warehouse_id: int):
    warehouse = get_warehouse(db, warehouse_id)
    occupied = get_warehouse_occupancy(db, warehouse_id)
    available = max(warehouse.capacity - occupied, 0)

    utilization = (
        occupied / warehouse.capacity * 100
        if warehouse.capacity > 0 else 0
    )

    return {
        "warehouse_id": warehouse.id,
        "capacity": warehouse.capacity,
        "occupied_quantity": occupied,
        "available_capacity": available,
        "utilization_percentage": round(utilization, 2)
    }
