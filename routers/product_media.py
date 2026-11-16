from fastapi import APIRouter, Depends, File, Form, Query, UploadFile, status
from sqlalchemy.orm import Session

from database.connection import get_db
from schemas.product_media import ProductMediaResponse
from services.product_media_service import (
    upload_product_media,
    list_product_media,
    delete_product_media
)
from utils.dependencies import get_current_user
from utils.permissions import require_roles


router = APIRouter(
    prefix="/product-media",
    tags=["MODULE 10 - Product Images & Documents"]
)


@router.post(
    "/upload/{product_id}",
    response_model=ProductMediaResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[
        Depends(require_roles(
            "SUPER_ADMIN",
            "ADMIN",
            "PRODUCT_MANAGER"
        ))
    ]
)
def upload_media(
    product_id: int,
    file: UploadFile = File(...),
    media_type: str = Form(...),
    is_primary: bool = Form(False),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    return upload_product_media(
        db,
        product_id,
        file,
        media_type,
        is_primary
    )


@router.get(
    "/product/{product_id}",
    response_model=list[ProductMediaResponse]
)
def get_product_media(
    product_id: int,
    media_type: str | None = Query(None),
    db: Session = Depends(get_db)
):
    return list_product_media(db, product_id, media_type)


@router.delete(
    "/{media_id}",
    dependencies=[
        Depends(require_roles(
            "SUPER_ADMIN",
            "ADMIN",
            "PRODUCT_MANAGER"
        ))
    ]
)
def remove_product_media(
    media_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    return delete_product_media(db, media_id)
