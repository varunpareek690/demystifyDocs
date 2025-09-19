from fastapi import APIRouter, Depends, HTTPException
from models.response import Response
from models.auth import User
from api.deps import get_current_user

router = APIRouter()

@router.post("/", response_model=Response)
async def chat(current_user: User = Depends(get_current_user)):
    """Chat with AI about legal documents (placeholder)."""
    return Response(
        success=True,
        message="Chat endpoint - Coming soon",
        data={"status": "placeholder", "user_id": current_user.uid}
    )

@router.get("/history", response_model=Response)
async def get_chat_history(current_user: User = Depends(get_current_user)):
    """Get chat history (placeholder)."""
    return Response(
        success=True,
        message="Chat history endpoint - Coming soon",
        data={"status": "placeholder", "user_id": current_user.uid}
    )
