from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from utils.permissions import ROLES


class UserCreate(BaseModel):
    first_name: str = Field(min_length=2, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    email: EmailStr
    phone: str = Field(min_length=10, max_length=20)
    password: str = Field(min_length=8, max_length=128)
    role: str = "CUSTOMER"


class UserUpdate(BaseModel):
    first_name: Optional[str] = Field(default=None, min_length=2, max_length=100)
    last_name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(default=None, min_length=10, max_length=20)


class UserRoleUpdate(BaseModel):
    role: str


class UserStatusUpdate(BaseModel):
    is_active: bool


class UserManagementResponse(BaseModel):
    id: int
    first_name: str
    last_name: str
    email: EmailStr
    phone: str
    role: str
    is_active: bool
    is_email_verified: bool

    model_config = ConfigDict(from_attributes=True)
