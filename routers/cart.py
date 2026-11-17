from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from utils.dependencies import get_db
from utils.permissions import require_roles
from schemas.cart import (
    CartItemCreate,
    CartItemUpdate,
    ShoppingCartResponse
)
from services.cart_service import (
    get_cart,
    add_cart_item,
    update_cart_item,
    remove_cart_item
)

router = APIRouter(
    prefix="/cart",
    tags=["MODULE 17 - Shopping Cart Management"]
)

customer_access = require_roles("SUPER_ADMIN", "ADMIN", "CUSTOMER")


@router.get("/", response_model=ShoppingCartResponse)
def retrieve_cart(
    db: Session = Depends(get_db),
    current_user=Depends(customer_access)
):
    return get_cart(db, current_user.id)


@router.post(
    "/items",
    response_model=ShoppingCartResponse,
    status_code=status.HTTP_201_CREATED
)
def add_item(
    payload: CartItemCreate,
    db: Session = Depends(get_db),
    current_user=Depends(customer_access)
):
    return add_cart_item(
        db,
        current_user.id,
        payload.product_id,
        payload.variant_id,
        payload.quantity
    )


@router.patch(
    "/items/{item_id}",
    response_model=ShoppingCartResponse
)
def update_item(
    item_id: int,
    payload: CartItemUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(customer_access)
):
    return update_cart_item(
        db,
        current_user.id,
        item_id,
        payload.quantity
    )


@router.delete(
    "/items/{item_id}",
    response_model=ShoppingCartResponse
)
def delete_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(customer_access)
):
    return remove_cart_item(
        db,
        current_user.id,
        item_id
    )
