from pydantic import BaseModel, ConfigDict, Field


class CategoryCreate(BaseModel):
    parent_id: int | None = None
    name: str = Field(min_length=2, max_length=150)
    slug: str = Field(min_length=2, max_length=180, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    description: str | None = None
    image_url: str | None = Field(default=None, max_length=500)
    is_active: bool = True


class CategoryUpdate(BaseModel):
    parent_id: int | None = None
    name: str | None = Field(default=None, min_length=2, max_length=150)
    slug: str | None = Field(default=None, min_length=2, max_length=180, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    description: str | None = None
    image_url: str | None = Field(default=None, max_length=500)
    is_active: bool | None = None


class CategoryResponse(BaseModel):
    id: int
    parent_id: int | None
    name: str
    slug: str
    description: str | None
    image_url: str | None
    is_active: bool

    model_config = ConfigDict(from_attributes=True)
