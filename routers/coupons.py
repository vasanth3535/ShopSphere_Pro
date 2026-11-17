from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from utils.dependencies import get_db
from utils.permissions import require_roles
from schemas.coupon import (
    CouponCreate,
    CouponUpdate,
    CouponStatusUpdate,
    CouponResponse
)
from services.coupon_service import (
    create_coupon,
    list_coupons,
    get_coupon,
    update_coupon,
    update_coupon_status
)

router = APIRouter(
    prefix="/coupons",
    tags=["MODULE 20 - Coupon Management"]
)

coupon_management_access = require_roles(
    "SUPER_ADMIN",
    "ADMIN",
    "FINANCE_MANAGER"
)


@router.post(
    "/",
    response_model=CouponResponse,
    status_code=status.HTTP_201_CREATED
)
def create_new_coupon(
    payload: CouponCreate,
    db: Session = Depends(get_db),
    current_user=Depends(coupon_management_access)
):
    return create_coupon(db, payload)


@router.get(
    "/",
    response_model=list[CouponResponse]
)
def retrieve_coupons(
    active_only: bool = Query(default=False),
    db: Session = Depends(get_db),
    current_user=Depends(coupon_management_access)
):
    return list_coupons(db, active_only)


@router.get(
    "/{coupon_id}",
    response_model=CouponResponse
)
def retrieve_coupon(
    coupon_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(coupon_management_access)
):
    return get_coupon(db, coupon_id)


@router.patch(
    "/{coupon_id}",
    response_model=CouponResponse
)
def modify_coupon(
    coupon_id: int,
    payload: CouponUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(coupon_management_access)
):
    return update_coupon(db, coupon_id, payload)


@router.patch(
    "/{coupon_id}/status",
    response_model=CouponResponse
)
def modify_coupon_status(
    coupon_id: int,
    payload: CouponStatusUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(coupon_management_access)
):
    return update_coupon_status(
        db,
        coupon_id,
        payload.is_active
    )
