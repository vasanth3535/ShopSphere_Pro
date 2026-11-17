from uuid import uuid4
from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from models.inventory import Inventory, InventoryMovement
from models.inventory_transfer import InventoryTransfer
from models.inventory_transfer_history import InventoryTransferHistory
from models.warehouse import Warehouse
from models.warehouse_inventory import WarehouseInventory
from schemas.inventory_transfer import (
    InventoryTransferCreate,
    InventoryTransferDispatch,
    InventoryTransferReceive,
    InventoryTransferCancel
)


def get_transfer(db: Session, transfer_id: int, lock: bool = False):
    query = db.query(InventoryTransfer).filter(
        InventoryTransfer.id == transfer_id
    )

    if lock:
        query = query.with_for_update()

    transfer = query.first()

    if not transfer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Inventory transfer not found"
        )

    return transfer


def get_warehouse_stock(
    db: Session,
    warehouse_id: int,
    inventory_id: int,
    lock: bool = False
):
    query = db.query(WarehouseInventory).filter(
        WarehouseInventory.warehouse_id == warehouse_id,
        WarehouseInventory.inventory_id == inventory_id
    )

    if lock:
        query = query.with_for_update()

    return query.first()


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


def get_warehouse_occupancy(db: Session, warehouse_id: int):
    stocks = db.query(WarehouseInventory).filter(
        WarehouseInventory.warehouse_id == warehouse_id
    ).with_for_update().all()

    return sum(stock.total_quantity for stock in stocks)


def add_transfer_history(
    db: Session,
    transfer_id: int,
    previous_status: str | None,
    new_status: str,
    quantity: int,
    user_id: int,
    notes: str | None = None
):
    history = InventoryTransferHistory(
        transfer_id=transfer_id,
        previous_status=previous_status,
        new_status=new_status,
        quantity=quantity,
        performed_by=user_id,
        notes=notes
    )
    db.add(history)


def create_transfer(
    db: Session,
    data: InventoryTransferCreate,
    user_id: int
):
    source = get_warehouse(db, data.source_warehouse_id)
    destination = get_warehouse(db, data.destination_warehouse_id)

    if not source.is_active or not destination.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Both warehouses must be active"
        )

    inventory = db.query(Inventory).filter(
        Inventory.id == data.inventory_id
    ).first()

    if not inventory:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Inventory record not found"
        )

    source_stock = get_warehouse_stock(
        db,
        data.source_warehouse_id,
        data.inventory_id,
        lock=True
    )

    if not source_stock:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Inventory is not available in the source warehouse"
        )

    if source_stock.available_quantity < data.requested_quantity:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Insufficient available stock in source warehouse"
        )

    destination_occupied = get_warehouse_occupancy(
        db,
        destination.id
    )

    if data.requested_quantity > destination.capacity - destination_occupied:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Insufficient destination warehouse capacity"
        )

    transfer = InventoryTransfer(
        transfer_code=f"TRF-{uuid4().hex[:12].upper()}",
        source_warehouse_id=source.id,
        destination_warehouse_id=destination.id,
        inventory_id=data.inventory_id,
        requested_quantity=data.requested_quantity,
        status="REQUESTED",
        notes=data.notes,
        requested_by=user_id
    )

    db.add(transfer)
    db.flush()

    add_transfer_history(
        db,
        transfer.id,
        None,
        "REQUESTED",
        data.requested_quantity,
        user_id,
        data.notes
    )

    db.commit()
    db.refresh(transfer)
    return transfer


def list_transfers(
    db: Session,
    transfer_status: str | None = None,
    warehouse_id: int | None = None
):
    query = db.query(InventoryTransfer)

    if transfer_status:
        query = query.filter(
            InventoryTransfer.status == transfer_status
        )

    if warehouse_id:
        query = query.filter(
            (InventoryTransfer.source_warehouse_id == warehouse_id)
            | (InventoryTransfer.destination_warehouse_id == warehouse_id)
        )

    return query.order_by(
        InventoryTransfer.id.desc()
    ).all()


def dispatch_transfer(
    db: Session,
    transfer_id: int,
    data: InventoryTransferDispatch,
    user_id: int
):
    transfer = get_transfer(db, transfer_id, lock=True)

    if transfer.status != "REQUESTED":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only requested transfers can be dispatched"
        )

    if data.dispatched_quantity > transfer.requested_quantity:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Dispatched quantity cannot exceed requested quantity"
        )

    source_stock = get_warehouse_stock(
        db,
        transfer.source_warehouse_id,
        transfer.inventory_id,
        lock=True
    )

    if not source_stock or source_stock.available_quantity < data.dispatched_quantity:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Insufficient available stock for dispatch"
        )

    source_stock.total_quantity -= data.dispatched_quantity
    source_stock.available_quantity -= data.dispatched_quantity

    transfer.dispatched_quantity = data.dispatched_quantity
    transfer.dispatched_by = user_id
    transfer.dispatched_at = datetime.now()
    transfer.status = "DISPATCHED"

    add_transfer_history(
        db,
        transfer.id,
        "REQUESTED",
        "DISPATCHED",
        data.dispatched_quantity,
        user_id,
        data.notes
    )

    inventory_movement = InventoryMovement(
        inventory_id=transfer.inventory_id,
        movement_type="TRANSFER_OUT",
        quantity=data.dispatched_quantity,
        previous_quantity=source_stock.total_quantity + data.dispatched_quantity,
        new_quantity=source_stock.total_quantity,
        reason="Stock dispatched to another warehouse",
        reference=transfer.transfer_code,
        performed_by=user_id
    )

    db.add(inventory_movement)
    db.commit()
    db.refresh(transfer)
    return transfer


def receive_transfer(
    db: Session,
    transfer_id: int,
    data: InventoryTransferReceive,
    user_id: int
):
    transfer = get_transfer(db, transfer_id, lock=True)

    if transfer.status not in ("DISPATCHED", "PARTIALLY_RECEIVED"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This transfer cannot receive stock"
        )

    remaining_quantity = (
        transfer.dispatched_quantity - transfer.received_quantity
    )

    if data.received_quantity > remaining_quantity:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Only {remaining_quantity} units remain to be received"
        )

    destination = get_warehouse(db, transfer.destination_warehouse_id)

    if not destination.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Destination warehouse is inactive"
        )

    destination_occupied = get_warehouse_occupancy(
        db,
        destination.id
    )

    if data.received_quantity > destination.capacity - destination_occupied:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Insufficient destination warehouse capacity"
        )

    destination_stock = get_warehouse_stock(
        db,
        destination.id,
        transfer.inventory_id,
        lock=True
    )

    if not destination_stock:
        destination_stock = WarehouseInventory(
            warehouse_id=destination.id,
            inventory_id=transfer.inventory_id,
            total_quantity=0,
            reserved_quantity=0,
            available_quantity=0
        )
        db.add(destination_stock)
        db.flush()

    destination_stock.total_quantity += data.received_quantity
    destination_stock.available_quantity += data.received_quantity

    previous_status = transfer.status
    transfer.received_quantity += data.received_quantity

    if transfer.received_quantity == transfer.dispatched_quantity:
        transfer.status = "RECEIVED"
        transfer.received_at = datetime.now()
    else:
        transfer.status = "PARTIALLY_RECEIVED"

    transfer.received_by = user_id

    add_transfer_history(
        db,
        transfer.id,
        previous_status,
        transfer.status,
        data.received_quantity,
        user_id,
        data.notes
    )

    db.add(
        InventoryMovement(
            inventory_id=transfer.inventory_id,
            movement_type="TRANSFER_IN",
            quantity=data.received_quantity,
            previous_quantity=destination_stock.total_quantity - data.received_quantity,
            new_quantity=destination_stock.total_quantity,
            reason="Stock received from another warehouse",
            reference=transfer.transfer_code,
            performed_by=user_id
        )
    )

    db.commit()
    db.refresh(transfer)
    return transfer


def cancel_transfer(
    db: Session,
    transfer_id: int,
    data: InventoryTransferCancel,
    user_id: int
):
    transfer = get_transfer(db, transfer_id, lock=True)

    if transfer.status != "REQUESTED":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only requested transfers can be cancelled"
        )

    transfer.status = "CANCELLED"

    add_transfer_history(
        db,
        transfer.id,
        "REQUESTED",
        "CANCELLED",
        0,
        user_id,
        data.notes
    )

    db.commit()
    db.refresh(transfer)
    return transfer


def get_transfer_history(db: Session, transfer_id: int):
    get_transfer(db, transfer_id)

    return db.query(InventoryTransferHistory).filter(
        InventoryTransferHistory.transfer_id == transfer_id
    ).order_by(
        InventoryTransferHistory.created_at.desc(),
        InventoryTransferHistory.id.desc()
    ).all()
