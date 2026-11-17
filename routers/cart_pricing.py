from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from utils.dependencies import get_db
from utils.permissions import require_roles
from schemas.cart_pricing import (
    CartPriceCalculationRequest,
    CartPriceCalculationResponse
)
from services.cart_pricing_service import calculate_cart_price

router = APIRouter(
    prefix="/cart/pricing",
    tags=["MODULE 18 - Cart Price Calculation"]
)

cart_pricing_access = require_roles(
    "SUPER_ADMIN",
    "ADMIN",
    "CUSTOMER"
)


@router.post(
    "/checkout-summary",
    response_model=CartPriceCalculationResponse
)
def checkout_summary(
    payload: CartPriceCalculationRequest,
    db: Session = Depends(get_db),
    current_user=Depends(cart_pricing_access)
):
    return calculate_cart_price(
        db,
        current_user.id,
        payload.coupon_code
    )
