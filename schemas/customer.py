from pydantic import BaseModel, ConfigDict, EmailStr, Field


class CustomerRegistration(BaseModel):
    first_name: str = Field(min_length=2, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    email: EmailStr
    phone: str = Field(min_length=10, max_length=20)
    password: str = Field(min_length=8, max_length=128)


class EmailVerificationRequest(BaseModel):
    verification_token: str


class CustomerRegistrationResponse(BaseModel):
    id: int
    first_name: str
    last_name: str
    email: EmailStr
    phone: str
    role: str
    is_active: bool
    is_email_verified: bool

    model_config = ConfigDict(from_attributes=True)
