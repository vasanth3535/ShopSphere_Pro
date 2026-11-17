from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from database.connection import get_db
from schemas.product_attribute import (
    ProductAttributeCreate,
    ProductAttributeUpdate,
    ProductAttributeResponse,
    ProductAttributeValueCreate,
    ProductAttributeValueUpdate,
    ProductAttributeValueResponse
)
from services.product_attribute_service import (
    create_attribute,
    list_attributes,
    get_attribute,
    update_attribute,
    create_attribute_value,
    list_product_attribute_values,
    update_attribute_value,
    delete_attribute_value,
    filter_products_by_attribute
)
from schemas.product import ProductResponse
from utils.permissions import require_roles


router = APIRouter(
    prefix="/product-attributes",
    tags=["MODULE 11 - Product Attributes"]
)


@router.post(
    "/",
    response_model=ProductAttributeResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_roles("SUPER_ADMIN", "ADMIN", "PRODUCT_MANAGER"))]
)
def add_attribute(
    data: ProductAttributeCreate,
    db: Session = Depends(get_db)
):
    return create_attribute(db, data)


@router.get("/", response_model=list[ProductAttributeResponse])
def get_attributes(
    category_id: int | None = Query(None, gt=0),
    include_inactive: bool = False,
    db: Session = Depends(get_db)
):
    return list_attributes(db, category_id, include_inactive)


@router.get("/filter", response_model=list[ProductResponse])
def get_products_by_attribute(
    attribute_id: int = Query(gt=0),
    value: str = Query(min_length=1, max_length=1000),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    return filter_products_by_attribute(
        db, attribute_id, value, page, page_size
    )


@router.post(
    "/values",
    response_model=ProductAttributeValueResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_roles("SUPER_ADMIN", "ADMIN", "PRODUCT_MANAGER"))]
)
def assign_attribute_value(
    data: ProductAttributeValueCreate,
    db: Session = Depends(get_db)
):
    return create_attribute_value(
        db, data.product_id, data.attribute_id, data.value
    )


@router.get(
    "/products/{product_id}/values",
    response_model=list[ProductAttributeValueResponse]
)
def get_product_attribute_values(
    product_id: int,
    db: Session = Depends(get_db)
):
    return list_product_attribute_values(db, product_id)


@router.put(
    "/values/{value_id}",
    response_model=ProductAttributeValueResponse,
    dependencies=[Depends(require_roles("SUPER_ADMIN", "ADMIN", "PRODUCT_MANAGER"))]
)
def edit_attribute_value(
    value_id: int,
    data: ProductAttributeValueUpdate,
    db: Session = Depends(get_db)
):
    return update_attribute_value(db, value_id, data.value)


@router.delete(
    "/values/{value_id}",
    dependencies=[Depends(require_roles("SUPER_ADMIN", "ADMIN", "PRODUCT_MANAGER"))]
)
def remove_attribute_value(
    value_id: int,
    db: Session = Depends(get_db)
):
    return delete_attribute_value(db, value_id)


@router.get("/{attribute_id}", response_model=ProductAttributeResponse)
def get_attribute_details(
    attribute_id: int,
    db: Session = Depends(get_db)
):
    return get_attribute(db, attribute_id)


@router.put(
    "/{attribute_id}",
    response_model=ProductAttributeResponse,
    dependencies=[Depends(require_roles("SUPER_ADMIN", "ADMIN", "PRODUCT_MANAGER"))]
)
def edit_attribute(
    attribute_id: int,
    data: ProductAttributeUpdate,
    db: Session = Depends(get_db)
):
    return update_attribute(db, attribute_id, data)
