from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from models.product import Product
from models.product_variant import ProductVariant
from schemas.product_variant import ProductVariantCreate, ProductVariantUpdate


def create_variant(db: Session, data: ProductVariantCreate):
    product = db.get(Product, data.product_id)

    if not product or not product.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Active product not found"
        )

    variant = ProductVariant(**data.model_dump())
    db.add(variant)

    try:
        db.commit()
        db.refresh(variant)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Variant SKU already exists"
        )

    return variant


def list_variants(
    db: Session,
    product_id: int | None = None,
    include_inactive: bool = False
):
    query = select(ProductVariant)

    if product_id is not None:
        query = query.where(ProductVariant.product_id == product_id)

    if not include_inactive:
        query = query.where(ProductVariant.is_active.is_(True))

    return db.scalars(query.order_by(ProductVariant.created_at.desc())).all()


def get_variant(db: Session, variant_id: int):
    variant = db.get(ProductVariant, variant_id)

    if not variant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product variant not found"
        )

    return variant


def update_variant(db: Session, variant_id: int, data: ProductVariantUpdate):
    variant = get_variant(db, variant_id)
    update_data = data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(variant, field, value)

    try:
        db.commit()
        db.refresh(variant)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Variant SKU already exists"
        )

    return variant


def delete_variant(db: Session, variant_id: int):
    variant = get_variant(db, variant_id)
    variant.is_active = False
    db.commit()

    return {"message": "Product variant deactivated successfully"}
