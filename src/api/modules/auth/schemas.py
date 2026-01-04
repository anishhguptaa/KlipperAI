from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime


class RegisterRequest(BaseModel):
    """Request schema for user registration"""
    name: Optional[str] = Field(None, max_length=150, description="User's full name")
    email: EmailStr = Field(..., description="User's email address")
    password: str = Field(..., min_length=8, description="User's password (minimum 8 characters)")


class LoginRequest(BaseModel):
    """Request schema for user login"""
    email: EmailStr = Field(..., description="User's email address")
    password: str = Field(..., description="User's password")


class AuthResponse(BaseModel):
    """Response schema for authentication endpoints"""
    message: str = Field(..., description="Success message")
    user: "UserResponse" = Field(..., description="User information")


class UserResponse(BaseModel):
    """Response schema for user information"""
    id: int = Field(..., description="User ID")
    name: Optional[str] = Field(None, description="User's full name")
    email: str = Field(..., description="User's email address")
    created_at: datetime = Field(..., description="Account creation timestamp")

    class Config:
        from_attributes = True


class ErrorResponse(BaseModel):
    """Error response schema"""
    detail: str = Field(..., description="Error message")
    error_code: Optional[str] = Field(None, description="Error code")


# Update forward reference
AuthResponse.model_rebuild()
