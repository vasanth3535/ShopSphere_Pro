from fastapi import HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from models.product import Product
from models.category import Category
from models.brand import Brand
from schemas.product import ProductCreate, ProductUpdate


def validate_category_and_brand(db: Session, category_id: int, brand_id: int | None):
    category = db.get(Category, category_id)

    if not category or not category.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Selected category does not exist or is inactive"
        )

    if brand_id is not None:
        brand = db.get(Brand, brand_id)

        if not brand or not brand.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Selected brand does not exist or is inactive"
            )


def create_product(db: Session, data: ProductCreate):
    validate_category_and_brand(db, data.category_id, data.brand_id)

    product = Product(**data.model_dump())
    db.add(product)

    try:
        db.commit()
        db.refresh(product)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Product SKU or slug already exists"
        )

    return product


def list_products(
    db: Session,
    search: str | None = None,
    category_id: int | None = None,
    brand_id: int | None = None,
    min_price: float | None = None,
    max_price: float | None = None,
    include_inactive: bool = False,
    page: int = 1,
    page_size: int = 20
):
    query = select(Product)

    if not include_inactive:
        query = query.where(Product.is_active.is_(True))

    if search:
        term = f"%{search.strip()}%"
        query = query.where(
            or_(
                Product.name.ilike(term),
                Product.sku.ilike(term),
                Product.description.ilike(term)
            )
        )

    if category_id is not None:
        query = query.where(Product.category_id == category_id)

    if brand_id is not None:
        query = query.where(Product.brand_id == brand_id)

    if min_price is not None:
        query = query.where(Product.base_price >= min_price)

    if max_price is not None:
        query = query.where(Product.base_price <= max_price)

    query = query.order_by(Product.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    return db.scalars(query).all()


def get_product(db: Session, product_id: int):
    product = db.get(Product, product_id)

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )

    return product


def update_product(db: Session, product_id: int, data: ProductUpdate):
    product = get_product(db, product_id)
    update_data = data.model_dump(exclude_unset=True)

    category_id = update_data.get("category_id", product.category_id)
    brand_id = update_data.get("brand_id", product.brand_id)

    validate_category_and_brand(db, category_id, brand_id)

    for field, value in update_data.items():
        setattr(product, field, value)

    try:
        db.commit()
        db.refresh(product)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Product SKU or slug already exists"
        )

    return product


def delete_product(db: Session, product_id: int):
    product = get_product(db, product_id)
    product.is_active = False
    db.commit()

    return {"message": "Product deactivated successfully"}
