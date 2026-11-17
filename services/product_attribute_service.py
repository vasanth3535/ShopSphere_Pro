from decimal import Decimal, InvalidOperation

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from models.category import Category
from models.product import Product
from models.product_attribute import ProductAttribute, ProductAttributeValue
from schemas.product_attribute import ProductAttributeCreate, ProductAttributeUpdate


def validate_category(db: Session, category_id: int):
    category = db.get(Category, category_id)

    if not category or not category.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Selected category does not exist or is inactive"
        )

    return category


def validate_attribute_value(attribute: ProductAttribute, value: str):
    value = value.strip()

    if not value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Attribute value cannot be empty"
        )

    if attribute.data_type == "NUMBER":
        try:
            Decimal(value)
        except InvalidOperation:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Attribute value must be a valid number"
            )

    elif attribute.data_type == "BOOLEAN":
        if value.lower() not in {"true", "false"}:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Attribute value must be true or false"
            )
        value = value.lower()

    elif attribute.data_type == "SELECT":
        if not attribute.allowed_values:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="SELECT attributes must have allowed values"
            )

        matched = next(
            (item for item in attribute.allowed_values if item.lower() == value.lower()),
            None
        )

        if matched is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid value. Allowed values: {', '.join(attribute.allowed_values)}"
            )

        value = matched

    return value


def create_attribute(db: Session, data: ProductAttributeCreate):
    validate_category(db, data.category_id)

    if data.data_type == "SELECT" and not data.allowed_values:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="SELECT attributes require allowed values"
        )

    if data.data_type != "SELECT" and data.allowed_values:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Allowed values are only supported for SELECT attributes"
        )

    attribute = ProductAttribute(**data.model_dump())
    db.add(attribute)

    try:
        db.commit()
        db.refresh(attribute)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Attribute code already exists in this category"
        )

    return attribute


def list_attributes(
    db: Session,
    category_id: int | None = None,
    include_inactive: bool = False
):
    query = select(ProductAttribute)

    if category_id is not None:
        query = query.where(ProductAttribute.category_id == category_id)

    if not include_inactive:
        query = query.where(ProductAttribute.is_active.is_(True))

    return db.scalars(query.order_by(ProductAttribute.name)).all()


def get_attribute(db: Session, attribute_id: int):
    attribute = db.get(ProductAttribute, attribute_id)

    if not attribute:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product attribute not found"
        )

    return attribute


def update_attribute(db: Session, attribute_id: int, data: ProductAttributeUpdate):
    attribute = get_attribute(db, attribute_id)
    update_data = data.model_dump(exclude_unset=True)

    new_type = update_data.get("data_type", attribute.data_type)
    new_values = update_data.get("allowed_values", attribute.allowed_values)

    if new_type == "SELECT" and not new_values:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="SELECT attributes require allowed values"
        )

    if new_type != "SELECT" and new_values:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Allowed values are only supported for SELECT attributes"
        )

    if "data_type" in update_data or "allowed_values" in update_data:
        existing_values = db.scalars(
            select(ProductAttributeValue).where(
                ProductAttributeValue.attribute_id == attribute_id
            )
        ).all()

        for item in existing_values:
            validate_attribute_value(
                ProductAttribute(
                    data_type=new_type,
                    allowed_values=new_values
                ),
                item.value
            )

    for field, value in update_data.items():
        setattr(attribute, field, value)

    db.commit()
    db.refresh(attribute)

    return attribute


def create_attribute_value(db: Session, product_id: int, attribute_id: int, value: str):
    product = db.get(Product, product_id)

    if not product or not product.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found or inactive"
        )

    attribute = get_attribute(db, attribute_id)

    if not attribute.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Product attribute is inactive"
        )

    if product.category_id != attribute.category_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Attribute does not belong to the product category"
        )

    validated_value = validate_attribute_value(attribute, value)

    existing = db.scalar(
        select(ProductAttributeValue).where(
            ProductAttributeValue.product_id == product_id,
            ProductAttributeValue.attribute_id == attribute_id
        )
    )

    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Attribute value already assigned to this product"
        )

    item = ProductAttributeValue(
        product_id=product_id,
        attribute_id=attribute_id,
        value=validated_value
    )

    db.add(item)
    db.commit()
    db.refresh(item)

    return item


def list_product_attribute_values(db: Session, product_id: int):
    product = db.get(Product, product_id)

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )

    return db.scalars(
        select(ProductAttributeValue).where(
            ProductAttributeValue.product_id == product_id
        ).order_by(ProductAttributeValue.id)
    ).all()


def update_attribute_value(db: Session, value_id: int, value: str):
    item = db.get(ProductAttributeValue, value_id)

    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product attribute value not found"
        )

    attribute = get_attribute(db, item.attribute_id)
    item.value = validate_attribute_value(attribute, value)

    db.commit()
    db.refresh(item)

    return item


def delete_attribute_value(db: Session, value_id: int):
    item = db.get(ProductAttributeValue, value_id)

    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product attribute value not found"
        )

    db.delete(item)
    db.commit()

    return {"message": "Product attribute value removed successfully"}


def filter_products_by_attribute(
    db: Session,
    attribute_id: int,
    value: str,
    page: int = 1,
    page_size: int = 20
):
    attribute = get_attribute(db, attribute_id)

    if not attribute.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Product attribute is inactive"
        )

    validated_value = validate_attribute_value(attribute, value)

    query = (
        select(Product)
        .join(
            ProductAttributeValue,
            ProductAttributeValue.product_id == Product.id
        )
        .where(
            ProductAttributeValue.attribute_id == attribute_id,
            ProductAttributeValue.value == validated_value,
            Product.is_active.is_(True)
        )
        .order_by(Product.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )

    return db.scalars(query).unique().all()
