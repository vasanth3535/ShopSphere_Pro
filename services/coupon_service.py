from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from models.coupon import Coupon
from schemas.coupon import CouponCreate, CouponUpdate


def get_coupon_or_404(db: Session, coupon_id: int):
    coupon = db.scalar(
        select(Coupon).where(Coupon.id == coupon_id)
    )

    if not coupon:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Coupon not found"
        )

    return coupon


def create_coupon(db: Session, payload: CouponCreate):
    existing = db.scalar(
        select(Coupon).where(Coupon.code == payload.code)
    )

    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Coupon code already exists"
        )

    coupon = Coupon(**payload.model_dump())

    db.add(coupon)

    try:
        db.commit()
        db.refresh(coupon)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Coupon code already exists"
        )

    return coupon


def list_coupons(db: Session, active_only: bool = False):
    query = select(Coupon).order_by(Coupon.created_at.desc())

    if active_only:
        query = query.where(Coupon.is_active.is_(True))

    return db.scalars(query).all()


def get_coupon(db: Session, coupon_id: int):
    return get_coupon_or_404(db, coupon_id)


def update_coupon(
    db: Session,
    coupon_id: int,
    payload: CouponUpdate
):
    coupon = get_coupon_or_404(db, coupon_id)
    updates = payload.model_dump(exclude_unset=True)

    discount_type = updates.get("discount_type", coupon.discount_type)
    discount_value = updates.get("discount_value", coupon.discount_value)
    valid_from = updates.get("valid_from", coupon.valid_from)
    valid_until = updates.get("valid_until", coupon.valid_until)

    if discount_type == "PERCENTAGE" and discount_value > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Percentage discount cannot exceed 100"
        )

    if valid_until <= valid_from:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Coupon end date must be after start date"
        )

    for field, value in updates.items():
        setattr(coupon, field, value)

    try:
        db.commit()
        db.refresh(coupon)
    except Exception:
        db.rollback()
        raise

    return coupon


def update_coupon_status(
    db: Session,
    coupon_id: int,
    is_active: bool
):
    coupon = get_coupon_or_404(db, coupon_id)
    coupon.is_active = is_active
    db.commit()
    db.refresh(coupon)

    return coupon


def validate_coupon(
    db: Session,
    code: str,
    subtotal
):
    coupon = db.scalar(
        select(Coupon).where(Coupon.code == code.strip().upper())
    )

    if not coupon:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid coupon code"
        )

    now = datetime.now()

    if not coupon.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Coupon is inactive"
        )

    if now < coupon.valid_from or now > coupon.valid_until:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Coupon is outside its validity period"
        )

    if subtotal < coupon.minimum_purchase:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Minimum purchase amount is {coupon.minimum_purchase}"
        )

    if coupon.discount_type == "PERCENTAGE":
        discount = subtotal * coupon.discount_value / 100
    else:
        discount = coupon.discount_value

    discount = min(discount, subtotal)

    return coupon, discount
