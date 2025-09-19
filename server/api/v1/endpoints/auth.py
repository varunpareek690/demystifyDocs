from fastapi import APIRouter, Depends, HTTPException, status
from models.auth import UserRegister, UserLogin, Token, User
from models.response import Response, ErrorResponse
from services.auth_service import AuthService
from api.deps import get_current_user

router = APIRouter()

@router.post("/register", response_model=Response)
async def register(user_data: UserRegister):
    """Register a new user."""
    try:
        auth_service = AuthService()
        result = await auth_service.register_user(user_data)
        
        return Response(
            success=True,
            message="User registered successfully",
            data=result
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/login", response_model=Response)
async def login(login_data: UserLogin):
    """Authenticate user login."""
    try:
        auth_service = AuthService()
        result = await auth_service.authenticate_user(login_data)
        
        return Response(
            success=True,
            message="Login successful",
            data=result
        )
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))

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
