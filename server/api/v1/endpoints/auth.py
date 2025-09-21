from fastapi import APIRouter, Depends, HTTPException, status
from models.auth import GoogleOAuthLogin, User
from models.response import Response
from services.auth_service import AuthService
from api.deps import get_current_user
from core.config import settings

router = APIRouter()

@router.post("/google", response_model=Response)
async def google_oauth_login(oauth_data: GoogleOAuthLogin):
    """Authenticate user via Google OAuth. Creates account if user doesn't exist."""
    try:
        auth_service = AuthService()
        result = await auth_service.authenticate_google_user(oauth_data)
        
        return Response(
            success=True,
            message="Google authentication successful",
            data=result
        )
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))

@router.get("/google/config", response_model=Response)
async def get_google_config():
    """Get Google OAuth configuration for frontend."""
    return Response(
        success=True,
        message="Google OAuth configuration",
        data={
            "client_id": settings.GOOGLE_CLIENT_ID,
            "redirect_uri": settings.GOOGLE_OAUTH_REDIRECT_URI
        }
    )

@router.post("/logout", response_model=Response)
async def logout(current_user: User = Depends(get_current_user)):
    """Logout user (client-side token removal)."""
    return Response(
        success=True,
        message="Logout successful",
        data={"user_id": current_user.uid}
    )

@router.get("/me", response_model=Response)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information."""
    return Response(
        success=True,
        message="User information retrieved",
        data={"user": current_user}
    )