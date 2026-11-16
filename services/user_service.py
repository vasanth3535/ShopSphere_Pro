from fastapi import HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from models.user import User
from schemas.user import UserCreate, UserUpdate
from utils.permissions import ROLES
from utils.security import hash_password


def create_user(data: UserCreate, db: Session) -> User:
    if data.role not in ROLES:
        raise HTTPException(status_code=400, detail="Invalid user role")

    existing = db.scalar(
        select(User).where(
            or_(User.email == data.email, User.phone == data.phone)
        )
    )

    if existing:
        raise HTTPException(status_code=409, detail="Email or phone already exists")

    user = User(
        first_name=data.first_name,
        last_name=data.last_name,
        email=data.email,
        phone=data.phone,
        password_hash=hash_password(data.password),
        role=data.role
    )

    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def list_users(
    db: Session,
    search: str = None,
    role: str = None,
    is_active: bool = None,
    skip: int = 0,
    limit: int = 50
):
    query = select(User)

    if search:
        term = f"%{search}%"
        query = query.where(
            or_(
                User.first_name.ilike(term),
                User.last_name.ilike(term),
                User.email.ilike(term),
                User.phone.ilike(term)
            )
        )

    if role:
        if role not in ROLES:
            raise HTTPException(status_code=400, detail="Invalid user role")
        query = query.where(User.role == role)

    if is_active is not None:
        query = query.where(User.is_active == is_active)

    return list(
        db.scalars(
            query.order_by(User.id.desc()).offset(skip).limit(limit)
        ).all()
    )


def get_user(user_id: int, db: Session) -> User:
    user = db.get(User, user_id)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user


def update_user(user_id: int, data: UserUpdate, db: Session) -> User:
    user = get_user(user_id, db)
    updates = data.model_dump(exclude_unset=True)

    for field in ("email", "phone"):
        value = updates.get(field)
        if value is not None:
            existing = db.scalar(
                select(User).where(
                    getattr(User, field) == value,
                    User.id != user_id
                )
            )
            if existing:
                raise HTTPException(
                    status_code=409,
                    detail=f"{field.capitalize()} already exists"
                )

    for field, value in updates.items():
        setattr(user, field, value)

    db.commit()
    db.refresh(user)
    return user


def update_user_role(user_id: int, role: str, db: Session) -> User:
    if role not in ROLES:
        raise HTTPException(status_code=400, detail="Invalid user role")

    user = get_user(user_id, db)
    user.role = role
    db.commit()
    db.refresh(user)
    return user


def update_user_status(user_id: int, is_active: bool, db: Session) -> User:
    user = get_user(user_id, db)
    user.is_active = is_active
    db.commit()
    db.refresh(user)
    return user
