from datetime import datetime
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from models.product import Product
from models.product_pricing import ProductPricing, ProductPriceHistory
from schemas.product_pricing import ProductPricingCreate, ProductPricingUpdate


def get_product_or_404(db: Session, product_id: int):
    product = db.get(Product, product_id)

    if not product or not product.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Active product not found"
        )

    return product


def validate_price_period(
    db: Session,
    product_id: int,
    valid_from: datetime,
    valid_until: datetime | None,
    exclude_id: int | None = None
):
    query = select(ProductPricing).where(
        ProductPricing.product_id == product_id,
        ProductPricing.is_active.is_(True)
    )

    if exclude_id is not None:
        query = query.where(ProductPricing.id != exclude_id)

    existing_periods = db.scalars(query).all()

    for existing in existing_periods:
        existing_end = existing.valid_until or datetime.max
        new_end = valid_until or datetime.max

        if valid_from < existing_end and existing.valid_from < new_end:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Pricing validity period overlaps an existing active price"
            )


def record_price_history(
    db: Session,
    product_id: int,
    pricing_id: int | None,
    previous_base_price: Decimal | None,
    new_base_price: Decimal,
    previous_sale_price: Decimal | None,
    new_sale_price: Decimal | None,
    change_reason: str | None,
    user_id: int
):
    history = ProductPriceHistory(
        product_id=product_id,
        pricing_id=pricing_id,
        previous_base_price=previous_base_price,
        new_base_price=new_base_price,
        previous_sale_price=previous_sale_price,
        new_sale_price=new_sale_price,
        change_reason=change_reason,
        changed_by=user_id
    )

    db.add(history)


def create_product_pricing(
    db: Session,
    data: ProductPricingCreate,
    user_id: int
):
    product = get_product_or_404(db, data.product_id)

    validate_price_period(
        db,
        data.product_id,
        data.valid_from,
        data.valid_until
    )

    pricing = ProductPricing(
        product_id=data.product_id,
        base_price=data.base_price,
        sale_price=data.sale_price,
        valid_from=data.valid_from,
        valid_until=data.valid_until,
        created_by=user_id
    )

    db.add(pricing)
    db.flush()

    record_price_history(
        db,
        product.id,
        pricing.id,
        product.base_price,
        data.base_price,
        None,
        data.sale_price,
        data.change_reason,
        user_id
    )

    try:
        db.commit()
        db.refresh(pricing)
    except Exception:
        db.rollback()
        raise

    return pricing


def list_product_pricing(
    db: Session,
    product_id: int,
    include_inactive: bool = False
):
    get_product_or_404(db, product_id)

    query = select(ProductPricing).where(
        ProductPricing.product_id == product_id
    )

    if not include_inactive:
        query = query.where(ProductPricing.is_active.is_(True))

    return db.scalars(
        query.order_by(ProductPricing.valid_from.desc())
    ).all()


def get_product_pricing(db: Session, pricing_id: int):
    pricing = db.get(ProductPricing, pricing_id)

    if not pricing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product pricing record not found"
        )

    return pricing


def update_product_pricing(
    db: Session,
    pricing_id: int,
    data: ProductPricingUpdate,
    user_id: int
):
    pricing = get_product_pricing(db, pricing_id)
    update_data = data.model_dump(exclude_unset=True)
    change_reason = update_data.pop("change_reason", None)

    product = get_product_or_404(db, pricing.product_id)

    new_base_price = update_data.get("base_price", pricing.base_price)
    new_sale_price = update_data.get("sale_price", pricing.sale_price)
    new_valid_from = update_data.get("valid_from", pricing.valid_from)
    new_valid_until = update_data.get("valid_until", pricing.valid_until)
    new_is_active = update_data.get("is_active", pricing.is_active)

    if new_sale_price is not None and new_sale_price >= new_base_price:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Sale price must be lower than base price"
        )

    if new_valid_until is not None and new_valid_until <= new_valid_from:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="valid_until must be later than valid_from"
        )

    if new_is_active:
        validate_price_period(
            db,
            pricing.product_id,
            new_valid_from,
            new_valid_until,
            pricing.id
        )

    previous_base_price = pricing.base_price
    previous_sale_price = pricing.sale_price

    for field, value in update_data.items():
        setattr(pricing, field, value)

    if (
        previous_base_price != new_base_price
        or previous_sale_price != new_sale_price
    ):
        record_price_history(
            db,
            product.id,
            pricing.id,
            previous_base_price,
            new_base_price,
            previous_sale_price,
            new_sale_price,
            change_reason,
            user_id
        )

    try:
        db.commit()
        db.refresh(pricing)
    except Exception:
        db.rollback()
        raise

    return pricing


def get_current_product_price(db: Session, product_id: int):
    product = get_product_or_404(db, product_id)
    now = datetime.now()

    query = select(ProductPricing).where(
        ProductPricing.product_id == product_id,
        ProductPricing.is_active.is_(True),
        ProductPricing.valid_from <= now
    )

    pricing_records = db.scalars(
        query.order_by(ProductPricing.valid_from.desc())
    ).all()

    pricing = next(
        (
            item for item in pricing_records
            if item.valid_until is None or item.valid_until > now
        ),
        None
    )

    if not pricing:
        return {
            "product_id": product.id,
            "base_price": product.base_price,
            "sale_price": None,
            "effective_price": product.base_price,
            "pricing_source": "PRODUCT_BASE_PRICE",
            "valid_from": None,
            "valid_until": None
        }

    effective_price = (
        pricing.sale_price
        if pricing.sale_price is not None
        else pricing.base_price
    )

    return {
        "product_id": product.id,
        "base_price": pricing.base_price,
        "sale_price": pricing.sale_price,
        "effective_price": effective_price,
        "pricing_source": "SCHEDULED",
        "valid_from": pricing.valid_from,
        "valid_until": pricing.valid_until
    }


def get_product_price_history(
    db: Session,
    product_id: int,
    page: int = 1,
    page_size: int = 20
):
    get_product_or_404(db, product_id)

    query = (
        select(ProductPriceHistory)
        .where(ProductPriceHistory.product_id == product_id)
        .order_by(ProductPriceHistory.changed_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )

    return db.scalars(query).all()
