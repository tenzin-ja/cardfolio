from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class UserRegister(BaseModel):
    """Validate the email and password submitted during registration."""

    # Reject any extra fields that aren't listed below
    model_config = ConfigDict(extra="forbid")

    # Check that this looks like an email address, not that the inbox exists
    email: EmailStr = Field(max_length=320)

    # repr=False hides the password when printing this object
    # This does not hash it or hide it when using model_dump()
    password: str = Field(min_length=15, max_length=128, repr=False)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        """Make the email lowercase after checking its format"""

        # Treat Jam@example.com and jam@example.com as the same account
        return value.lower()


class UserResponse(BaseModel):
    """Return public account details without exposing a password or hash"""

    # Allow these values to come directly from a saved User object
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    created_at: datetime

class UserLogin(BaseModel):
    '''Credentials submitted when signing in'''

    model_config = ConfigDict(extra="forbid")

    email: EmailStr = Field(max_length=320)
    password: str = Field(min_length=1,max_length=128, repr=False)

    @field_validator("email")
    @classmethod
    def normalize_emails(cls,value: str)-> str:
        # to keep the same format as registration
        return value.lower()

class TokenResponse(BaseModel):
    '''Return the access token and its type after a successful login'''
    access_token: str
    # Access tokens are sent as Bearer tokens in the Authorization header
    token_type: Literal["bearer"] = "bearer"

