from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from database.connection import get_db
from models.user import User
from schemas.user import (
    UserCreate,
    UserManagementResponse,
    UserRoleUpdate,
    UserStatusUpdate,
    UserUpdate,
)
from services.user_service import (
    create_user,
    get_user,
    list_users,
    update_user,
    update_user_role,
    update_user_status,
)
from utils.permissions import require_roles

router = APIRouter(
    prefix="/users",
    tags=["MODULE 2 - User Management"]
)

admin_access = require_roles("SUPER_ADMIN", "ADMIN")
super_admin_access = require_roles("SUPER_ADMIN")


@router.post("/", response_model=UserManagementResponse, status_code=status.HTTP_201_CREATED)
def create_new_user(
    data: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_access)
):
    return create_user(data, db)


@router.get("/", response_model=list[UserManagementResponse])
def get_all_users(
    search: str = Query(default=None, max_length=100),
    role: str = Query(default=None),
    is_active: bool = Query(default=None),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_access)
):
    return list_users(db, search, role, is_active, skip, limit)


@router.get("/{user_id}", response_model=UserManagementResponse)
def get_user_details(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_access)
):
    return get_user(user_id, db)


@router.put("/{user_id}", response_model=UserManagementResponse)
def edit_user(
    user_id: int,
    data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_access)
):
    return update_user(user_id, data, db)


@router.patch("/{user_id}/role", response_model=UserManagementResponse)
def change_user_role(
    user_id: int,
    data: UserRoleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(super_admin_access)
):
    return update_user_role(user_id, data.role, db)


@router.patch("/{user_id}/status", response_model=UserManagementResponse)
def change_user_status(
    user_id: int,
    data: UserStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_access)
):
    return update_user_status(user_id, data.is_active, db)
