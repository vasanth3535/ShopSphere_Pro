from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from database.connection import get_db
from schemas.product_pricing import (
    ProductPricingCreate,
    ProductPricingUpdate,
    ProductPricingResponse,
    ProductPriceHistoryResponse,
    ProductCurrentPriceResponse
)
from services.product_pricing_service import (
    create_product_pricing,
    list_product_pricing,
    get_product_pricing,
    update_product_pricing,
    get_current_product_price,
    get_product_price_history
)
from utils.dependencies import get_current_user
from utils.permissions import require_roles


router = APIRouter(
    prefix="/product-pricing",
    tags=["MODULE 12 - Product Pricing"]
)

pricing_roles = ["SUPER_ADMIN", "ADMIN", "PRODUCT_MANAGER", "FINANCE_MANAGER"]


@router.post(
    "/",
    response_model=ProductPricingResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_roles(*pricing_roles))]
)
def create_pricing(
    data: ProductPricingCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    return create_product_pricing(db, data, current_user.id)


@router.get("/products/{product_id}/current", response_model=ProductCurrentPriceResponse)
def get_current_price(
    product_id: int,
    db: Session = Depends(get_db)
):
    return get_current_product_price(db, product_id)


@router.get(
    "/products/{product_id}/history",
    response_model=list[ProductPriceHistoryResponse],
    dependencies=[Depends(require_roles(*pricing_roles))]
)
def get_price_history(
    product_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    return get_product_price_history(db, product_id, page, page_size)


@router.get(
    "/products/{product_id}",
    response_model=list[ProductPricingResponse],
    dependencies=[Depends(require_roles(*pricing_roles))]
)
def get_product_pricing_records(
    product_id: int,
    include_inactive: bool = False,
    db: Session = Depends(get_db)
):
    return list_product_pricing(db, product_id, include_inactive)


@router.get(
    "/{pricing_id}",
    response_model=ProductPricingResponse,
    dependencies=[Depends(require_roles(*pricing_roles))]
)
def get_pricing_record(
    pricing_id: int,
    db: Session = Depends(get_db)
):
    return get_product_pricing(db, pricing_id)


@router.put(
    "/{pricing_id}",
    response_model=ProductPricingResponse,
    dependencies=[Depends(require_roles(*pricing_roles))]
)
def edit_pricing(
    pricing_id: int,
    data: ProductPricingUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    return update_product_pricing(db, pricing_id, data, current_user.id)
