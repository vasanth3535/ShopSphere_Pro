from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from database.connection import get_db
from schemas.customer import CustomerRegistration, EmailVerificationRequest
from services.customer_service import register_customer, verify_customer_email

router = APIRouter(
    prefix="/customers",
    tags=["MODULE 3 - Customer Registration"]
)


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(
    data: CustomerRegistration,
    db: Session = Depends(get_db)
):
    return register_customer(data, db)


@router.post("/verify-email")
def verify_email(
    data: EmailVerificationRequest,
    db: Session = Depends(get_db)
):
    return verify_customer_email(data.verification_token, db)
