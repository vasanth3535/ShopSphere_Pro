from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from models.product import Product
from models.product_variant import ProductVariant
from models.inventory import Inventory, InventoryMovement
from schemas.inventory import InventoryCreate, InventoryAdjustment


def get_product(db: Session, product_id: int):
    product = db.get(Product, product_id)

    if not product or not product.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Active product not found"
        )

    return product


def validate_variant(db: Session, product_id: int, variant_id: int | None):
    if variant_id is None:
        return

    variant = db.get(ProductVariant, variant_id)

    if not variant or not variant.is_active or variant.product_id != product_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Variant does not belong to the selected active product"
        )


def get_inventory(db: Session, inventory_id: int, lock: bool = False):
    query = select(Inventory).where(Inventory.id == inventory_id)

    if lock:
        query = query.with_for_update()

    inventory = db.scalar(query)

    if not inventory:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Inventory record not found"
        )

    return inventory


def get_inventory_by_product(
    db: Session,
    product_id: int,
    variant_id: int | None = None
):
    query = select(Inventory).where(
        Inventory.product_id == product_id,
        Inventory.variant_id == variant_id
    )

    return db.scalar(query)


def create_inventory(
    db: Session,
    data: InventoryCreate,
    user_id: int
):
    get_product(db, data.product_id)
    validate_variant(db, data.product_id, data.variant_id)

    existing = get_inventory_by_product(
        db,
        data.product_id,
        data.variant_id
    )

    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Inventory record already exists for this product and variant"
        )

    inventory = Inventory(
        product_id=data.product_id,
        variant_id=data.variant_id,
        total_quantity=data.initial_quantity,
        reserved_quantity=0,
        available_quantity=data.initial_quantity
    )

    db.add(inventory)
    db.flush()

    if data.initial_quantity > 0:
        db.add(
            InventoryMovement(
                inventory_id=inventory.id,
                movement_type="STOCK_IN",
                quantity=data.initial_quantity,
                previous_quantity=0,
                new_quantity=data.initial_quantity,
                reason="Initial stock",
                performed_by=user_id
            )
        )

    try:
        db.commit()
        db.refresh(inventory)
    except Exception:
        db.rollback()
        raise

    return inventory


def adjust_inventory(
    db: Session,
    inventory_id: int,
    data: InventoryAdjustment,
    user_id: int
):
    inventory = get_inventory(db, inventory_id, lock=True)

    previous_quantity = inventory.total_quantity

    if data.movement_type == "STOCK_IN":
        inventory.total_quantity += data.quantity
        inventory.available_quantity += data.quantity

    elif data.movement_type == "STOCK_OUT":
        if data.quantity > inventory.available_quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Insufficient available stock for this reduction"
            )

        inventory.total_quantity -= data.quantity
        inventory.available_quantity -= data.quantity

    db.add(
        InventoryMovement(
            inventory_id=inventory.id,
            movement_type=data.movement_type,
            quantity=data.quantity,
            previous_quantity=previous_quantity,
            new_quantity=inventory.total_quantity,
            reason=data.reason,
            reference=data.reference,
            performed_by=user_id
        )
    )

    try:
        db.commit()
        db.refresh(inventory)
    except Exception:
        db.rollback()
        raise

    return inventory


def reserve_inventory(
    db: Session,
    inventory_id: int,
    quantity: int,
    user_id: int
):
    inventory = get_inventory(db, inventory_id, lock=True)

    if quantity > inventory.available_quantity:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Insufficient available stock for reservation"
        )

    inventory.available_quantity -= quantity
    inventory.reserved_quantity += quantity

    db.add(
        InventoryMovement(
            inventory_id=inventory.id,
            movement_type="RESERVE",
            quantity=quantity,
            previous_quantity=inventory.total_quantity,
            new_quantity=inventory.total_quantity,
            reason="Stock reserved",
            performed_by=user_id
        )
    )

    try:
        db.commit()
        db.refresh(inventory)
    except Exception:
        db.rollback()
        raise

    return inventory


def release_inventory(
    db: Session,
    inventory_id: int,
    quantity: int,
    user_id: int
):
    inventory = get_inventory(db, inventory_id, lock=True)

    if quantity > inventory.reserved_quantity:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Release quantity exceeds reserved stock"
        )

    inventory.reserved_quantity -= quantity
    inventory.available_quantity += quantity

    db.add(
        InventoryMovement(
            inventory_id=inventory.id,
            movement_type="RELEASE",
            quantity=quantity,
            previous_quantity=inventory.total_quantity,
            new_quantity=inventory.total_quantity,
            reason="Reserved stock released",
            performed_by=user_id
        )
    )

    try:
        db.commit()
        db.refresh(inventory)
    except Exception:
        db.rollback()
        raise

    return inventory


def list_inventory(
    db: Session,
    product_id: int | None = None
):
    query = select(Inventory)

    if product_id is not None:
        query = query.where(Inventory.product_id == product_id)

    return db.scalars(query.order_by(Inventory.id.desc())).all()


def get_inventory_movements(
    db: Session,
    inventory_id: int,
    page: int = 1,
    page_size: int = 20
):
    get_inventory(db, inventory_id)

    query = (
        select(InventoryMovement)
        .where(InventoryMovement.inventory_id == inventory_id)
        .order_by(InventoryMovement.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )

    return db.scalars(query).all()
