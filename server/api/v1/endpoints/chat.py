from fastapi import APIRouter, Depends, HTTPException, Path
from models.response import Response
from models.auth import User
from models.chat import (
    ChatSessionCreate, SendMessageRequest, ChatSession, 
    ChatSessionWithMessages, ChatHistoryResponse
)
from services.chat_service import ChatService
from api.deps import get_current_user

router = APIRouter()

@router.post("/sessions", response_model=Response)
async def create_chat_session(
    session_data: ChatSessionCreate,
    current_user: User = Depends(get_current_user)
):
    """Create a new chat session with a document."""
    try:
        chat_service = ChatService()
        session = await chat_service.create_chat_session(current_user.uid, session_data)
        
        return Response(
            success=True,
            message="Chat session created successfully",
            data={"session": session}
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/sessions/{session_id}/messages", response_model=Response)
async def send_message(
    session_id: str,
    message_data: SendMessageRequest,
    current_user: User = Depends(get_current_user)
):
    """Send a message in a chat session."""
    try:
        chat_service = ChatService()
        user_message, ai_message = await chat_service.send_message(
            session_id, current_user.uid, message_data
        )
        
        return Response(
            success=True,
            message="Message sent successfully",
            data={
                "user_message": user_message,
                "ai_message": ai_message
            }
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/sessions/{session_id}", response_model=Response)
async def get_chat_session(
    session_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get a specific chat session with messages."""
    try:
        chat_service = ChatService()
        session_with_messages = await chat_service.get_chat_session_with_messages(
            session_id, current_user.uid
        )
        
        return Response(
            success=True,
            message="Chat session retrieved successfully",
            data={"session": session_with_messages}
        )
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/history", response_model=Response)
async def get_chat_history(current_user: User = Depends(get_current_user)):
    """Get user's chat history."""
    try:
        chat_service = ChatService()
        sessions = await chat_service.get_user_chat_history(current_user.uid)
        
        return Response(
            success=True,
            message="Chat history retrieved successfully",
            data={
                "sessions": sessions,
                "total_sessions": len(sessions)
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/sessions/{session_id}", response_model=Response)
async def delete_chat_session(
    session_id: str,
    current_user: User = Depends(get_current_user)
):
    """Delete a chat session."""
    try:
        chat_service = ChatService()
        await chat_service.delete_chat_session(session_id, current_user.uid)
        
        return Response(
            success=True,
            message="Chat session deleted successfully",
            data={"session_id": session_id}
        )
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))
