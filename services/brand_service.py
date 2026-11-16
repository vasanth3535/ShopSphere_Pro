from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from models.brand import Brand
from schemas.brand import BrandCreate, BrandUpdate


def create_brand(db: Session, data: BrandCreate):
    brand_data = data.model_dump(mode="json")
    brand = Brand(**brand_data)
    db.add(brand)

    try:
        db.commit()
        db.refresh(brand)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Brand name or slug already exists"
        )

    return brand


def list_brands(db: Session, include_inactive: bool = False):
    query = select(Brand).order_by(Brand.name)

    if not include_inactive:
        query = query.where(Brand.is_active.is_(True))

    return db.scalars(query).all()


def get_brand(db: Session, brand_id: int):
    brand = db.get(Brand, brand_id)

    if not brand:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Brand not found"
        )

    return brand


def update_brand(db: Session, brand_id: int, data: BrandUpdate):
    brand = get_brand(db, brand_id)
    update_data = data.model_dump(exclude_unset=True, mode="json")

    for field, value in update_data.items():
        setattr(brand, field, value)

    try:
        db.commit()
        db.refresh(brand)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Brand name or slug already exists"
        )

    return brand


def delete_brand(db: Session, brand_id: int):
    brand = get_brand(db, brand_id)
    db.delete(brand)
    db.commit()

    return {"message": "Brand deleted successfully"}
