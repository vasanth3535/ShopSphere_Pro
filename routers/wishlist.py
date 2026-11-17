from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from utils.dependencies import get_db
from utils.permissions import require_roles
from schemas.wishlist import (
    WishlistCreate,
    WishlistItemResponse,
    WishlistResponse
)
from services.wishlist_service import (
    add_to_wishlist,
    get_wishlist,
    remove_from_wishlist
)

router = APIRouter(
    prefix="/wishlist",
    tags=["MODULE 19 - Wishlist Management"]
)

wishlist_access = require_roles(
    "SUPER_ADMIN",
    "ADMIN",
    "CUSTOMER"
)


@router.post(
    "/",
    response_model=WishlistItemResponse,
    status_code=status.HTTP_201_CREATED
)
def add_product(
    payload: WishlistCreate,
    db: Session = Depends(get_db),
    current_user=Depends(wishlist_access)
):
    return add_to_wishlist(
        db,
        current_user.id,
        payload.product_id
    )


@router.get(
    "/",
    response_model=WishlistResponse
)
def retrieve_wishlist(
    db: Session = Depends(get_db),
    current_user=Depends(wishlist_access)
):
    return get_wishlist(db, current_user.id)


@router.delete("/{product_id}")
def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(wishlist_access)
):
    return remove_from_wishlist(
        db,
        current_user.id,
        product_id
    )
