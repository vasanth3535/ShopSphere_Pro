import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from models.email_verification import EmailVerification
from models.user import User
from schemas.customer import CustomerRegistration
from utils.security import hash_password


def register_customer(data: CustomerRegistration, db: Session) -> dict:
    existing = db.scalar(
        select(User).where(
            or_(User.email == data.email, User.phone == data.phone)
        )
    )

    if existing:
        raise HTTPException(
            status_code=409,
            detail="Email or phone number is already registered"
        )

    customer = User(
        first_name=data.first_name,
        last_name=data.last_name,
        email=data.email,
        phone=data.phone,
        password_hash=hash_password(data.password),
        role="CUSTOMER",
        is_active=True,
        is_email_verified=False
    )

    try:
        db.add(customer)
        db.flush()

        verification_token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(
            verification_token.encode()
        ).hexdigest()

        verification = EmailVerification(
            user_id=customer.id,
            token_hash=token_hash,
            expires_at=datetime.now(timezone.utc).replace(tzinfo=None)
            + timedelta(hours=24)
        )

        db.add(verification)
        db.commit()
        db.refresh(customer)

        return {
            "customer": {
                "id": customer.id,
                "first_name": customer.first_name,
                "last_name": customer.last_name,
                "email": customer.email,
                "phone": customer.phone,
                "role": customer.role,
                "is_active": customer.is_active,
                "is_email_verified": customer.is_email_verified,
                "created_at": customer.created_at,
                "updated_at": customer.updated_at
            },
            "verification_token": verification_token,
            "message": "Registration successful. Verify your email within 24 hours."
        }

    except Exception:
        db.rollback()
        raise


def verify_customer_email(token: str, db: Session) -> dict:
    token_hash = hashlib.sha256(token.encode()).hexdigest()

    verification = db.scalar(
        select(EmailVerification).where(
            EmailVerification.token_hash == token_hash
        )
    )

    if not verification:
        raise HTTPException(
            status_code=400,
            detail="Invalid verification token"
        )

    if verification.verified_at:
        raise HTTPException(
            status_code=400,
            detail="Email is already verified"
        )

    now = datetime.now(timezone.utc).replace(tzinfo=None)

    if verification.expires_at < now:
        raise HTTPException(
            status_code=400,
            detail="Verification token has expired"
        )

    customer = db.get(User, verification.user_id)

    if not customer:
        raise HTTPException(
            status_code=404,
            detail="Customer not found"
        )

    try:
        customer.is_email_verified = True
        verification.verified_at = now
        db.commit()
    except Exception:
        db.rollback()
        raise

    return {
        "success": True,
        "message": "Email verified successfully"
    }
