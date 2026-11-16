from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from database.connection import get_db
from schemas.address import AddressCreate, AddressUpdate, AddressResponse
from services.address_service import (
    create_address,
    list_addresses,
    get_address,
    update_address,
    set_default_address,
    delete_address
)
from utils.dependencies import get_current_user


router = APIRouter(
    prefix="/addresses",
    tags=["MODULE 5 - Address Management"]
)


@router.post("/", response_model=AddressResponse, status_code=status.HTTP_201_CREATED)
def add_address(
    data: AddressCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    return create_address(db, current_user.id, data)


@router.get("/", response_model=list[AddressResponse])
def get_my_addresses(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    return list_addresses(db, current_user.id)


@router.get("/{address_id}", response_model=AddressResponse)
def get_my_address(
    address_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    return get_address(db, current_user.id, address_id)


@router.put("/{address_id}", response_model=AddressResponse)
def edit_address(
    address_id: int,
    data: AddressUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    return update_address(db, current_user.id, address_id, data)


@router.patch("/{address_id}/default", response_model=AddressResponse)
def make_default_address(
    address_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    return set_default_address(db, current_user.id, address_id)


@router.delete("/{address_id}")
def remove_address(
    address_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    return delete_address(db, current_user.id, address_id)
