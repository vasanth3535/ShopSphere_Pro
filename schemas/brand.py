from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class BrandCreate(BaseModel):
    name: str = Field(min_length=2, max_length=150)
    slug: str = Field(min_length=2, max_length=180, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    description: str | None = None
    logo_url: HttpUrl | None = None
    website_url: HttpUrl | None = None
    is_active: bool = True


class BrandUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=150)
    slug: str | None = Field(default=None, min_length=2, max_length=180, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    description: str | None = None
    logo_url: HttpUrl | None = None
    website_url: HttpUrl | None = None
    is_active: bool | None = None


class BrandResponse(BaseModel):
    id: int
    name: str
    slug: str
    description: str | None
    logo_url: str | None
    website_url: str | None
    is_active: bool

    model_config = ConfigDict(from_attributes=True)
