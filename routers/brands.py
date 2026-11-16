from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from database.connection import get_db
from schemas.brand import BrandCreate, BrandUpdate, BrandResponse
from services.brand_service import (
    create_brand,
    list_brands,
    get_brand,
    update_brand,
    delete_brand
)
from utils.dependencies import get_current_user
from utils.permissions import require_roles


router = APIRouter(
    prefix="/brands",
    tags=["MODULE 7 - Brand Management"]
)


@router.post(
    "/",
    response_model=BrandResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_roles("SUPER_ADMIN", "ADMIN", "PRODUCT_MANAGER"))]
)
def add_brand(
    data: BrandCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    return create_brand(db, data)


@router.get("/", response_model=list[BrandResponse])
def get_brands(
    include_inactive: bool = Query(False),
    db: Session = Depends(get_db)
):
    return list_brands(db, include_inactive)


@router.get("/{brand_id}", response_model=BrandResponse)
def get_brand_details(
    brand_id: int,
    db: Session = Depends(get_db)
):
    return get_brand(db, brand_id)


@router.put(
    "/{brand_id}",
    response_model=BrandResponse,
    dependencies=[Depends(require_roles("SUPER_ADMIN", "ADMIN", "PRODUCT_MANAGER"))]
)
def edit_brand(
    brand_id: int,
    data: BrandUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    return update_brand(db, brand_id, data)


@router.delete(
    "/{brand_id}",
    dependencies=[Depends(require_roles("SUPER_ADMIN", "ADMIN"))]
)
def remove_brand(
    brand_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    return delete_brand(db, brand_id)
