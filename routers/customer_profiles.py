from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database.connection import get_db
from models.user import User
from schemas.customer_profile import (
    CustomerProfileResponse,
    CustomerProfileUpdate,
)
from services.customer_profile_service import (
    deactivate_customer_account,
    get_customer_profile,
    update_customer_profile,
)
from utils.dependencies import get_current_user

router = APIRouter(
    prefix="/customer-profile",
    tags=["MODULE 4 - Customer Profile Management"]
)


@router.get("/me", response_model=CustomerProfileResponse)
def get_my_profile(
    current_user: User = Depends(get_current_user)
):
    return get_customer_profile(current_user)


@router.put("/me", response_model=CustomerProfileResponse)
def update_my_profile(
    data: CustomerProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return update_customer_profile(data, current_user, db)


@router.patch("/me/deactivate")
def deactivate_my_account(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return deactivate_customer_account(current_user, db)
