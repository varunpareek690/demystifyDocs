from fastapi import APIRouter, Depends, HTTPException, Path, Query
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
    """
    Create a new chat session with a document.
    Now includes initial AI message with document summary.
    """
    try:
        chat_service = ChatService()
        session = await chat_service.create_chat_session(current_user.uid, session_data)
        
        # Get suggested questions for the new session
        try:
            suggested_questions = await chat_service.get_session_suggested_questions(
                session.id, current_user.uid
            )
        except Exception:
            suggested_questions = []
        
        return Response(
            success=True,
            message="Chat session created successfully",
            data={
                "session": session,
                "suggested_questions": suggested_questions,
                "initial_message_created": True
            }
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/sessions/{session_id}/messages", response_model=Response)
async def send_message(
    session_id: str,
    message_data: SendMessageRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Send a message in a chat session using Vertex AI for contextual responses.
    """
    try:
        chat_service = ChatService()
        user_message, ai_message = await chat_service.send_message(
            session_id, current_user.uid, message_data
        )
        
        # Get updated session info
        session = await chat_service.get_chat_session(session_id, current_user.uid)
        
        return Response(
            success=True,
            message="Message sent successfully",
            data={
                "user_message": user_message,
                "ai_message": ai_message,
                "session_updated": session,
                "message_count": session.message_count
            }
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/sessions/{session_id}", response_model=Response)
async def get_chat_session(
    session_id: str,
    include_messages: bool = Query(True, description="Include chat messages"),
    message_limit: int = Query(50, ge=1, le=200, description="Maximum messages to return"),
    current_user: User = Depends(get_current_user)
):
    """
    Get a specific chat session with optional messages.
    Enhanced with document context and summary information.
    """
    try:
        chat_service = ChatService()
        
        if include_messages:
            session_with_messages = await chat_service.get_chat_session_with_messages(
                session_id, current_user.uid, limit=message_limit
            )
            
            user_message_count = sum(1 for msg in session_with_messages.messages if msg.role.value == 'user')
            suggested_questions = []
            
            if user_message_count == 0:
                try:
                    suggested_questions = await chat_service.get_session_suggested_questions(
                        session_id, current_user.uid
                    )
                except Exception:
                    pass
            
            return Response(
                success=True,
                message="Chat session retrieved successfully",
                data={
                    "session": session_with_messages,
                    "suggested_questions": suggested_questions,
                    "message_count": len(session_with_messages.messages),
                    "user_message_count": user_message_count
                }
            )
        else:
            session = await chat_service.get_chat_session(session_id, current_user.uid)
            return Response(
                success=True,
                message="Chat session retrieved successfully",
                data={"session": session}
            )
            
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/sessions/{session_id}/suggested-questions", response_model=Response)
async def get_session_suggested_questions(
    session_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get AI-generated suggested questions for a chat session."""
    try:
        chat_service = ChatService()
        questions = await chat_service.get_session_suggested_questions(session_id, current_user.uid)
        
        return Response(
            success=True,
            message="Suggested questions retrieved successfully",
            data={
                "suggested_questions": questions,
                "session_id": session_id
            }
        )
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/history", response_model=Response)
async def get_chat_history(
    include_preview: bool = Query(True, description="Include last message preview"),
    limit: int = Query(50, ge=1, le=100, description="Maximum sessions to return"),
    current_user: User = Depends(get_current_user)
):
    """
    Get user's chat history with enhanced metadata.
    """
    try:
        chat_service = ChatService()
        sessions = await chat_service.get_user_chat_history(current_user.uid)
        
        # Apply limit
        sessions = sessions[:limit]
        
        enhanced_sessions = []
        
        for session in sessions:
            session_data = {
                "id": session.id,
                "title": session.title,
                "document_id": session.document_id,
                "message_count": session.message_count,
                "created_at": session.created_at,
                "updated_at": session.updated_at,
                "is_active": session.is_active
            }
            
            if include_preview:
                try:
                    recent_messages = await chat_service._get_recent_messages(session.id, limit=3)
                    
                    last_user_message = None
                    last_ai_message = None
                    
                    for msg in reversed(recent_messages):
                        if msg['role'] == 'user' and not last_user_message:
                            last_user_message = msg['content'][:100] + ('...' if len(msg['content']) > 100 else '')
                        elif msg['role'] == 'ai' and not last_ai_message:
                            last_ai_message = msg['content'][:100] + ('...' if len(msg['content']) > 100 else '')
                    
                    session_data["preview"] = {
                        "last_user_message": last_user_message,
                        "last_ai_message": last_ai_message,
                        "total_exchanges": len([m for m in recent_messages if m['role'] == 'user'])
                    }
                except Exception:
                    session_data["preview"] = None
            
            enhanced_sessions.append(session_data)
        
        return Response(
            success=True,
            message="Chat history retrieved successfully",
            data={
                "sessions": enhanced_sessions,
                "total_sessions": len(enhanced_sessions),
                "showing_limit": limit
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/sessions/{session_id}/export", response_model=Response)
async def export_chat_session(
    session_id: str,
    format: str = Query("json", regex="^(json|txt|markdown)$", description="Export format"),
    current_user: User = Depends(get_current_user)
):
    """Export chat session in various formats."""
    try:
        chat_service = ChatService()
        session_with_messages = await chat_service.get_chat_session_with_messages(
            session_id, current_user.uid
        )
        
        if format == "json":
            export_data = {
                "session_info": {
                    "id": session_with_messages.session.id,
                    "title": session_with_messages.session.title,
                    "document_title": session_with_messages.document_title,
                    "created_at": session_with_messages.session.created_at.isoformat(),
                    "message_count": len(session_with_messages.messages)
                },
                "messages": [
                    {
                        "role": msg.role.value,
                        "content": msg.content,
                        "timestamp": msg.timestamp.isoformat()
                    }
                    for msg in session_with_messages.messages
                ]
            }
        
        elif format == "txt":
            lines = [
                f"Chat Session: {session_with_messages.session.title}",
                f"Document: {session_with_messages.document_title}",
                f"Created: {session_with_messages.session.created_at}",
                f"Messages: {len(session_with_messages.messages)}",
                "-" * 50,
                ""
            ]
            
            for msg in session_with_messages.messages:
                role_label = "You" if msg.role.value == "user" else "AI Assistant"
                lines.extend([
                    f"{role_label} ({msg.timestamp.strftime('%Y-%m-%d %H:%M')}):",
                    msg.content,
                    ""
                ])
            
            export_data = "\n".join(lines)
        
        elif format == "markdown":
            lines = [
                f"# {session_with_messages.session.title}",
                "",
                f"**Document:** {session_with_messages.document_title}  ",
                f"**Created:** {session_with_messages.session.created_at}  ",
                f"**Messages:** {len(session_with_messages.messages)}",
                "",
                "---",
                ""
            ]
            
            for msg in session_with_messages.messages:
                role_label = "🧑 **You**" if msg.role.value == "user" else "🤖 **AI Assistant**"
                lines.extend([
                    f"### {role_label}",
                    f"*{msg.timestamp.strftime('%Y-%m-%d %H:%M')}*",
                    "",
                    msg.content,
                    ""
                ])
            
            export_data = "\n".join(lines)
        
        return Response(
            success=True,
            message=f"Chat session exported as {format.upper()}",
            data={
                "export_data": export_data,
                "format": format,
                "session_id": session_id,
                "message_count": len(session_with_messages.messages)
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.delete("/sessions/{session_id}", response_model=Response)
async def delete_chat_session(
    session_id: str,
    current_user: User = Depends(get_current_user)
):
    """Delete a chat session and all its messages."""
    try:
        chat_service = ChatService()
        
        session = await chat_service.get_chat_session(session_id, current_user.uid)
        message_count = session.message_count
        
        await chat_service.delete_chat_session(session_id, current_user.uid)
        
        return Response(
            success=True,
            message="Chat session deleted successfully",
            data={
                "session_id": session_id,
                "deleted_messages": message_count,
                "session_title": session.title
            }
        )
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/stats", response_model=Response)
async def get_chat_stats(
    current_user: User = Depends(get_current_user)
):
    """Get user's chat usage statistics."""
    try:
        chat_service = ChatService()
        sessions = await chat_service.get_user_chat_history(current_user.uid)
        
        # Calculate stats
        total_sessions = len(sessions)
        total_messages = sum(session.message_count for session in sessions)
        active_sessions = len([s for s in sessions if s.is_active])
        
        from datetime import datetime, timedelta
        week_ago = datetime.utcnow() - timedelta(days=7)
        recent_sessions = len([s for s in sessions if s.updated_at > week_ago])
        
        most_active_session = None
        if sessions:
            most_active = max(sessions, key=lambda s: s.message_count)
            if most_active.message_count > 1:
                most_active_session = {
                    "id": most_active.id,
                    "title": most_active.title,
                    "message_count": most_active.message_count
                }
        
        return Response(
            success=True,
            message="Chat statistics retrieved successfully",
            data={
                "total_sessions": total_sessions,
                "total_messages": total_messages,
                "active_sessions": active_sessions,
                "recent_activity_7days": recent_sessions,
                "average_messages_per_session": round(total_messages / max(total_sessions, 1), 1),
                "most_active_session": most_active_session
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))