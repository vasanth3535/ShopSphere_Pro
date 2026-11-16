from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from database.connection import get_db
from schemas.category import CategoryCreate, CategoryUpdate, CategoryResponse
from services.category_service import (
    create_category,
    list_categories,
    get_category,
    update_category,
    delete_category
)
from utils.dependencies import get_current_user
from utils.permissions import require_roles


router = APIRouter(
    prefix="/categories",
    tags=["MODULE 6 - Product Category Management"]
)


@router.post(
    "/",
    response_model=CategoryResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_roles("SUPER_ADMIN", "ADMIN", "PRODUCT_MANAGER"))]
)
def add_category(
    data: CategoryCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    return create_category(db, data)


@router.get("/", response_model=list[CategoryResponse])
def get_categories(
    include_inactive: bool = Query(False),
    db: Session = Depends(get_db)
):
    return list_categories(db, include_inactive)


@router.get("/{category_id}", response_model=CategoryResponse)
def get_category_details(
    category_id: int,
    db: Session = Depends(get_db)
):
    return get_category(db, category_id)


@router.put(
    "/{category_id}",
    response_model=CategoryResponse,
    dependencies=[Depends(require_roles("SUPER_ADMIN", "ADMIN", "PRODUCT_MANAGER"))]
)
def edit_category(
    category_id: int,
    data: CategoryUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    return update_category(db, category_id, data)


@router.delete(
    "/{category_id}",
    dependencies=[Depends(require_roles("SUPER_ADMIN", "ADMIN"))]
)
def remove_category(
    category_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    return delete_category(db, category_id)
