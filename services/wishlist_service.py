from fastapi import HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from models.wishlist import Wishlist
from models.product import Product
from models.inventory import Inventory


def get_product_or_404(db: Session, product_id: int):
    product = db.scalar(
        select(Product).where(
            Product.id == product_id,
            Product.is_active.is_(True)
        )
    )

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Active product not found"
        )

    return product


def get_product_availability(db: Session, product_id: int) -> bool:
    available_stock = db.scalar(
        select(func.coalesce(func.sum(Inventory.available_quantity), 0))
        .where(Inventory.product_id == product_id)
    )

    return available_stock > 0


def add_to_wishlist(
    db: Session,
    customer_id: int,
    product_id: int
):
    get_product_or_404(db, product_id)

    if not get_product_availability(db, product_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Product is currently out of stock"
        )

    existing = db.scalar(
        select(Wishlist).where(
            Wishlist.customer_id == customer_id,
            Wishlist.product_id == product_id
        )
    )

    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Product already exists in wishlist"
        )

    wishlist_item = Wishlist(
        customer_id=customer_id,
        product_id=product_id
    )

    db.add(wishlist_item)

    try:
        db.commit()
        db.refresh(wishlist_item)
    except Exception:
        db.rollback()
        raise

    return wishlist_item


def get_wishlist(db: Session, customer_id: int):
    query = (
        select(Wishlist, Product)
        .join(Product, Product.id == Wishlist.product_id)
        .where(
            Wishlist.customer_id == customer_id,
            Product.is_active.is_(True)
        )
        .order_by(Wishlist.created_at.desc())
    )

    results = db.execute(query).all()

    items = []

    for wishlist_item, product in results:
        items.append({
            "wishlist_id": wishlist_item.id,
            "product_id": product.id,
            "product_name": product.name,
            "sku": product.sku,
            "base_price": product.base_price,
            "is_available": get_product_availability(db, product.id),
            "created_at": wishlist_item.created_at
        })

    return {
        "customer_id": customer_id,
        "total_items": len(items),
        "items": items
    }


def remove_from_wishlist(
    db: Session,
    customer_id: int,
    product_id: int
):
    wishlist_item = db.scalar(
        select(Wishlist).where(
            Wishlist.customer_id == customer_id,
            Wishlist.product_id == product_id
        )
    )

    if not wishlist_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found in wishlist"
        )

    db.delete(wishlist_item)
    db.commit()

    return {
        "message": "Product removed from wishlist",
        "product_id": product_id
    }
