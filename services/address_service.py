from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from models.address import Address
from schemas.address import AddressCreate, AddressUpdate


def create_address(db: Session, user_id: int, address_data: AddressCreate):
    if address_data.is_default:
        db.query(Address).filter(
            Address.user_id == user_id,
            Address.address_type == address_data.address_type,
            Address.is_default.is_(True)
        ).update({"is_default": False})

    address = Address(
        user_id=user_id,
        **address_data.model_dump()
    )

    db.add(address)
    db.commit()
    db.refresh(address)
    return address


def list_addresses(db: Session, user_id: int):
    return db.query(Address).filter(
        Address.user_id == user_id
    ).order_by(Address.is_default.desc(), Address.created_at.desc()).all()


def get_address(db: Session, user_id: int, address_id: int):
    address = db.query(Address).filter(
        Address.id == address_id,
        Address.user_id == user_id
    ).first()

    if not address:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Address not found"
        )

    return address


def update_address(
    db: Session,
    user_id: int,
    address_id: int,
    address_data: AddressUpdate
):
    address = get_address(db, user_id, address_id)
    update_data = address_data.model_dump(exclude_unset=True)

    if update_data.get("address_type") and address.is_default:
        db.query(Address).filter(
            Address.user_id == user_id,
            Address.address_type == update_data["address_type"],
            Address.is_default.is_(True),
            Address.id != address_id
        ).update({"is_default": False})

    for field, value in update_data.items():
        setattr(address, field, value)

    db.commit()
    db.refresh(address)
    return address


def set_default_address(db: Session, user_id: int, address_id: int):
    address = get_address(db, user_id, address_id)

    db.query(Address).filter(
        Address.user_id == user_id,
        Address.address_type == address.address_type,
        Address.is_default.is_(True)
    ).update({"is_default": False})

    address.is_default = True
    db.commit()
    db.refresh(address)
    return address


def delete_address(db: Session, user_id: int, address_id: int):
    address = get_address(db, user_id, address_id)

    db.delete(address)
    db.commit()

    return {"message": "Address deleted successfully"}
