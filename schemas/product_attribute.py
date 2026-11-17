from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ProductAttributeCreate(BaseModel):
    category_id: int = Field(gt=0)
    name: str = Field(min_length=2, max_length=100)
    code: str = Field(min_length=2, max_length=120, pattern=r"^[a-z][a-z0-9_]*$")
    data_type: Literal["STRING", "NUMBER", "BOOLEAN", "SELECT"] = "STRING"
    allowed_values: list[str] | None = None
    is_required: bool = False
    is_active: bool = True

    @field_validator("allowed_values")
    @classmethod
    def validate_allowed_values(cls, values):
        if values is not None:
            cleaned = [value.strip() for value in values]
            if not cleaned or any(not value for value in cleaned):
                raise ValueError("Allowed values cannot be empty")
            if len(cleaned) != len(set(cleaned)):
                raise ValueError("Allowed values must be unique")
            return cleaned
        return values


class ProductAttributeUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=100)
    data_type: Literal["STRING", "NUMBER", "BOOLEAN", "SELECT"] | None = None
    allowed_values: list[str] | None = None
    is_required: bool | None = None
    is_active: bool | None = None

    @field_validator("allowed_values")
    @classmethod
    def validate_allowed_values(cls, values):
        if values is not None:
            cleaned = [value.strip() for value in values]
            if not cleaned or any(not value for value in cleaned):
                raise ValueError("Allowed values cannot be empty")
            if len(cleaned) != len(set(cleaned)):
                raise ValueError("Allowed values must be unique")
            return cleaned
        return values


class ProductAttributeResponse(BaseModel):
    id: int
    category_id: int
    name: str
    code: str
    data_type: str
    allowed_values: list[str] | None
    is_required: bool
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProductAttributeValueCreate(BaseModel):
    product_id: int = Field(gt=0)
    attribute_id: int = Field(gt=0)
    value: str = Field(min_length=1, max_length=1000)


class ProductAttributeValueUpdate(BaseModel):
    value: str = Field(min_length=1, max_length=1000)


class ProductAttributeValueResponse(BaseModel):
    id: int
    product_id: int
    attribute_id: int
    value: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
