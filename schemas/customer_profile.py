from pydantic import BaseModel, ConfigDict, EmailStr, Field


class CustomerProfileUpdate(BaseModel):
    first_name: str | None = Field(default=None, min_length=2, max_length=100)
    last_name: str | None = Field(default=None, min_length=1, max_length=100)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, min_length=10, max_length=20)


class CustomerProfileResponse(BaseModel):
    id: int
    first_name: str
    last_name: str
    email: EmailStr
    phone: str
    role: str
    is_active: bool
    is_email_verified: bool

    model_config = ConfigDict(from_attributes=True)
