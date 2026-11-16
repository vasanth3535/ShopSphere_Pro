from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class ProductCreate(BaseModel):
    category_id: int = Field(gt=0)
    brand_id: int | None = Field(default=None, gt=0)
    name: str = Field(min_length=2, max_length=200)
    slug: str = Field(min_length=2, max_length=220, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    sku: str = Field(min_length=2, max_length=100)
    short_description: str | None = Field(default=None, max_length=500)
    description: str | None = None
    base_price: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    is_active: bool = True
    is_featured: bool = False


class ProductUpdate(BaseModel):
    category_id: int | None = Field(default=None, gt=0)
    brand_id: int | None = Field(default=None, gt=0)
    name: str | None = Field(default=None, min_length=2, max_length=200)
    slug: str | None = Field(default=None, min_length=2, max_length=220, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    sku: str | None = Field(default=None, min_length=2, max_length=100)
    short_description: str | None = Field(default=None, max_length=500)
    description: str | None = None
    base_price: Decimal | None = Field(default=None, gt=0, max_digits=12, decimal_places=2)
    is_active: bool | None = None
    is_featured: bool | None = None


class ProductResponse(BaseModel):
    id: int
    category_id: int
    brand_id: int | None
    name: str
    slug: str
    sku: str
    short_description: str | None
    description: str | None
    base_price: Decimal
    is_active: bool
    is_featured: bool

    model_config = ConfigDict(from_attributes=True)
