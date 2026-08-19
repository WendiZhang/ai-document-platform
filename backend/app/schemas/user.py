from datetime import datetime
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    field_validator,
)


class UserCreate(BaseModel):
    name: str = Field(
        min_length=2,
        max_length=100,
    )

    email: EmailStr

    password: str = Field(
        min_length=8,
        max_length=128,
    )

    @field_validator("name")
    @classmethod
    def clean_name(cls, value: str) -> str:
        cleaned_name = value.strip()

        if len(cleaned_name) < 2:
            raise ValueError(
                "Name must contain at least 2 characters"
            )

        return cleaned_name

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: EmailStr) -> str:
        return str(value).strip().lower()

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        if value != value.strip():
            raise ValueError(
                "Password cannot start or end with spaces"
            )

        if not any(character.isalpha() for character in value):
            raise ValueError(
                "Password must contain at least one letter"
            )

        if not any(character.isdigit() for character in value):
            raise ValueError(
                "Password must contain at least one number"
            )

        return value


class UserResponse(BaseModel):
    id: UUID
    name: str
    email: EmailStr
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )