from decimal import Decimal

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from database.connection import get_db
from schemas.product import ProductCreate, ProductUpdate, ProductResponse
from services.product_service import (
    create_product,
    list_products,
    get_product,
    update_product,
    delete_product
)
from utils.dependencies import get_current_user
from utils.permissions import require_roles


router = APIRouter(
    prefix="/products",
    tags=["MODULE 8 - Product Management"]
)


@router.post(
    "/",
    response_model=ProductResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_roles("SUPER_ADMIN", "ADMIN", "PRODUCT_MANAGER"))]
)
def add_product(
    data: ProductCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    return create_product(db, data)


@router.get("/", response_model=list[ProductResponse])
def get_products(
    search: str | None = None,
    category_id: int | None = Query(None, gt=0),
    brand_id: int | None = Query(None, gt=0),
    min_price: Decimal | None = Query(None, ge=0),
    max_price: Decimal | None = Query(None, ge=0),
    include_inactive: bool = False,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    if min_price is not None and max_price is not None and min_price > max_price:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=400,
            detail="min_price cannot be greater than max_price"
        )

    return list_products(
        db,
        search,
        category_id,
        brand_id,
        float(min_price) if min_price is not None else None,
        float(max_price) if max_price is not None else None,
        include_inactive,
        page,
        page_size
    )


@router.get("/{product_id}", response_model=ProductResponse)
def get_product_details(
    product_id: int,
    db: Session = Depends(get_db)
):
    return get_product(db, product_id)


@router.put(
    "/{product_id}",
    response_model=ProductResponse,
    dependencies=[Depends(require_roles("SUPER_ADMIN", "ADMIN", "PRODUCT_MANAGER"))]
)
def edit_product(
    product_id: int,
    data: ProductUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    return update_product(db, product_id, data)


@router.delete(
    "/{product_id}",
    dependencies=[Depends(require_roles("SUPER_ADMIN", "ADMIN"))]
)
def remove_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    return delete_product(db, product_id)
