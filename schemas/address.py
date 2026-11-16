from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class AddressCreate(BaseModel):
    address_type: Literal["BILLING", "SHIPPING"]
    full_name: str = Field(min_length=2, max_length=150)
    phone: str = Field(min_length=10, max_length=20)
    address_line_1: str = Field(min_length=5, max_length=255)
    address_line_2: str | None = Field(default=None, max_length=255)
    city: str = Field(min_length=2, max_length=100)
    state: str = Field(min_length=2, max_length=100)
    postal_code: str = Field(min_length=4, max_length=20)
    country: str = Field(min_length=2, max_length=100)
    landmark: str | None = Field(default=None, max_length=255)
    is_default: bool = False


class AddressUpdate(BaseModel):
    address_type: Literal["BILLING", "SHIPPING"] | None = None
    full_name: str | None = Field(default=None, min_length=2, max_length=150)
    phone: str | None = Field(default=None, min_length=10, max_length=20)
    address_line_1: str | None = Field(default=None, min_length=5, max_length=255)
    address_line_2: str | None = Field(default=None, max_length=255)
    city: str | None = Field(default=None, min_length=2, max_length=100)
    state: str | None = Field(default=None, min_length=2, max_length=100)
    postal_code: str | None = Field(default=None, min_length=4, max_length=20)
    country: str | None = Field(default=None, min_length=2, max_length=100)
    landmark: str | None = Field(default=None, max_length=255)


class AddressResponse(BaseModel):
    id: int
    user_id: int
    address_type: str
    full_name: str
    phone: str
    address_line_1: str
    address_line_2: str | None
    city: str
    state: str
    postal_code: str
    country: str
    landmark: str | None
    is_default: bool

    model_config = ConfigDict(from_attributes=True)
