from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from models.user import User
from schemas.customer_profile import CustomerProfileUpdate


def get_customer_profile(current_user: User) -> User:
    if current_user.role != "CUSTOMER":
        raise HTTPException(status_code=403, detail="Customer access required")

    return current_user


def update_customer_profile(
    data: CustomerProfileUpdate,
    current_user: User,
    db: Session
) -> User:
    customer = get_customer_profile(current_user)
    updates = data.model_dump(exclude_unset=True)

    for field in ("email", "phone"):
        value = updates.get(field)

        if value is not None and value != getattr(customer, field):
            existing = db.scalar(
                select(User).where(
                    getattr(User, field) == value,
                    User.id != customer.id
                )
            )

            if existing:
                raise HTTPException(
                    status_code=409,
                    detail=f"{field.capitalize()} is already registered"
                )

    try:
        if updates.get("email") and updates["email"] != customer.email:
            customer.is_email_verified = False

        for field, value in updates.items():
            setattr(customer, field, value)

        db.commit()
        db.refresh(customer)
        return customer

    except Exception:
        db.rollback()
        raise


def deactivate_customer_account(
    current_user: User,
    db: Session
) -> dict:
    customer = get_customer_profile(current_user)

    if not customer.is_active:
        raise HTTPException(status_code=400, detail="Account is already deactivated")

    try:
        customer.is_active = False
        db.commit()
        return {
            "success": True,
            "message": "Customer account deactivated successfully"
        }
    except Exception:
        db.rollback()
        raise
