from pydantic import BaseModel, EmailStr
from typing import Optional

class GoogleOAuthLogin(BaseModel):
    """Model for Google OAuth login"""
    id_token: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

class User(BaseModel):
    uid: str
    email: str
    full_name: str
    created_at: str
    is_active: bool = True
    google_id: str
    picture: Optional[str] = None
    auth_provider: str = "google"