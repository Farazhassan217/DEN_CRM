
from datetime import datetime
from typing import Optional, List
from uuid import UUID

from pydantic import (
    BaseModel,
    EmailStr,
    Field,
    ConfigDict,
)

from ..core.roles import UserRole


# ============================================================
# USER BASE
# ============================================================

class UserBase(BaseModel):
    email: EmailStr

    full_name: str = Field(
        ...,
        min_length=1,
        max_length=255
    )

    phone: Optional[str] = None

    role: UserRole

    is_active: bool = True


# ============================================================
# USER CREATE
# ============================================================

class UserCreate(UserBase):
    password: str = Field(
        ...,
        min_length=8
    )

    # PostgreSQL UUID
    organization_id: Optional[UUID] = None

    # List of clinic IDs
    assigned_clinics: Optional[List[str]] = None


# ============================================================
# USER UPDATE
# ============================================================

class UserUpdate(BaseModel):
    full_name: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=255
    )

    phone: Optional[str] = None

    role: Optional[UserRole] = None

    is_active: Optional[bool] = None

    # PostgreSQL UUID
    organization_id: Optional[UUID] = None

    assigned_clinics: Optional[List[str]] = None


# ============================================================
# USER DATABASE RESPONSE
# ============================================================
# USER IN DB (internal only, never returned in API responses)
# ============================================================

class UserInDB(UserBase):
    id: UUID

    created_at: datetime

    updated_at: datetime

    organization_id: Optional[UUID] = None

    assigned_clinics: List[str] = Field(
        default_factory=list
    )

    model_config = ConfigDict(
        from_attributes=True
    )


# ============================================================
# USER WITH PASSWORD (internal only — for login verification)
# ============================================================

class UserWithPassword(UserInDB):
    """Internal model that includes the hashed password for login.
    NEVER expose this in API responses."""
    password: Optional[str] = None


# ============================================================
# USER (safe public model — password excluded)
# ============================================================

class User(UserInDB):
    pass


# ============================================================
# LOGIN
# ============================================================

class UserLogin(BaseModel):
    email: Optional[EmailStr] = None

    username: Optional[str] = None

    password: str = Field(
        ...,
        min_length=1
    )


# ============================================================
# TOKEN
# ============================================================

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    refresh_token: Optional[str] = None
    user: User


class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(..., description="The refresh token string")


class GoogleAuthRequest(BaseModel):
    id_token: str = Field(..., description="Google OAuth ID Token or JWT from Google Identity Services")
    clinic_id: Optional[str] = Field(None, description="Optional clinic ID to assign if new user")


# ============================================================
# TOKEN DATA
# ============================================================

class TokenData(BaseModel):
    user_id: Optional[UUID] = None
    email: Optional[EmailStr] = None
    role: Optional[UserRole] = None
    organization_id: Optional[UUID] = None
    assigned_clinics: Optional[List[str]] = None
    jti: Optional[str] = None
    token_type: Optional[str] = "access"

