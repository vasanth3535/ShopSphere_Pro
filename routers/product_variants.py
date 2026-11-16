from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from database.connection import get_db
from schemas.product_variant import (
    ProductVariantCreate,
    ProductVariantUpdate,
    ProductVariantResponse
)
from services.product_variant_service import (
    create_variant,
    list_variants,
    get_variant,
    update_variant,
    delete_variant
)
from utils.dependencies import get_current_user
from utils.permissions import require_roles


router = APIRouter(
    prefix="/product-variants",
    tags=["MODULE 9 - Product Variants"]
)


@router.post(
    "/",
    response_model=ProductVariantResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_roles("SUPER_ADMIN", "ADMIN", "PRODUCT_MANAGER", "INVENTORY_MANAGER"))]
)
def add_variant(
    data: ProductVariantCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    return create_variant(db, data)


@router.get("/", response_model=list[ProductVariantResponse])
def get_variants(
    product_id: int | None = Query(None, gt=0),
    include_inactive: bool = False,
    db: Session = Depends(get_db)
):
    return list_variants(db, product_id, include_inactive)


@router.get("/{variant_id}", response_model=ProductVariantResponse)
def get_variant_details(
    variant_id: int,
    db: Session = Depends(get_db)
):
    return get_variant(db, variant_id)


@router.put(
    "/{variant_id}",
    response_model=ProductVariantResponse,
    dependencies=[Depends(require_roles("SUPER_ADMIN", "ADMIN", "PRODUCT_MANAGER", "INVENTORY_MANAGER"))]
)
def edit_variant(
    variant_id: int,
    data: ProductVariantUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    return update_variant(db, variant_id, data)


@router.delete(
    "/{variant_id}",
    dependencies=[Depends(require_roles("SUPER_ADMIN", "ADMIN", "INVENTORY_MANAGER"))]
)
def remove_variant(
    variant_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    return delete_variant(db, variant_id)
