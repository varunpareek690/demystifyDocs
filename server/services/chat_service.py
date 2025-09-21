from typing import List, Optional
from datetime import datetime
from core.firebase_config import get_firestore_client
from models.chat import (
    ChatSession, ChatMessage, MessageRole, ChatSessionCreate, 
    SendMessageRequest, ChatSessionWithMessages
)
from services.document_service import DocumentService
from services.ai_service import AIService
from utils.exceptions import NotFoundError, ValidationError
import uuid

class ChatService:
    def __init__(self):
        self.db = get_firestore_client()
        self.chat_sessions_collection = self.db.collection('chat_sessions')
        self.chat_messages_collection = self.db.collection('chat_messages')
        self.document_service = DocumentService()
        self.ai_service = AIService()

    async def create_chat_session(self, user_id: str, session_data: ChatSessionCreate) -> ChatSession:
        """Create a new chat session with a document."""
        # Verify document exists and belongs to user
        document = await self.document_service.get_document_by_id(session_data.document_id, user_id)
        
        session_id = str(uuid.uuid4())
        title = session_data.title or f"Chat about {document.title}"
        
        session_dict = {
            'id': session_id,
            'user_id': user_id,
            'document_id': session_data.document_id,
            'title': title,
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow(),
            'message_count': 0,
            'is_active': True
        }

        # Save to Firestore
        self.chat_sessions_collection.document(session_id).set({
            **session_dict,
            'created_at': session_dict['created_at'].isoformat(),
            'updated_at': session_dict['updated_at'].isoformat()
        })

        # Create initial system message with document summary
        try:
            summary = await self.document_service.get_document_summary(session_data.document_id, user_id)
            system_content = f"""I have analyzed the document "{document.title}". Here's a summary:

{summary.summary}

Key Points:
{chr(10).join(f'• {point}' for point in summary.key_points)}

You can now ask me any questions about this document, and I'll help you understand its contents, implications, and answer any legal questions you might have."""
        except:
            system_content = f"""I have the document "{document.title}" available for discussion. You can ask me any questions about its contents, and I'll help you understand its implications and answer any legal questions you might have."""

        await self._add_message(session_id, MessageRole.AI, system_content)
        
        return ChatSession(**session_dict)

    async def send_message(self, session_id: str, user_id: str, message_request: SendMessageRequest) -> tuple[ChatMessage, ChatMessage]:
        """Send a message and get AI response."""
        # Verify session exists and belongs to user
        session = await self.get_chat_session(session_id, user_id)
        
        # Add user message
        user_message = await self._add_message(session_id, MessageRole.USER, message_request.message)
        
        # Get document context
        document = await self.document_service.get_document_by_id(session.document_id, user_id)
        
        # Get recent messages for context
        recent_messages = await self._get_recent_messages(session_id, limit=10)
        
        # Generate AI response
        ai_response_content = await self.ai_service.chat_with_document(
            document_content=document.content,
            document_title=document.title,
            user_message=message_request.message,
            chat_history=recent_messages
        )
        
        # Add AI response message
        ai_message = await self._add_message(session_id, MessageRole.AI, ai_response_content)
        
        # Update session
        await self._update_session_timestamp(session_id)
        
        return user_message, ai_message

    async def get_chat_session(self, session_id: str, user_id: str) -> ChatSession:
        """Get a specific chat session."""
        session_ref = self.chat_sessions_collection.document(session_id)
        session_doc = session_ref.get()
        
        if not session_doc.exists:
            raise NotFoundError("Chat session not found")
            
        session_data = session_doc.to_dict()
        
        # Verify ownership
        if session_data['user_id'] != user_id:
            raise NotFoundError("Chat session not found")

        session_data['created_at'] = datetime.fromisoformat(session_data['created_at'])
        session_data['updated_at'] = datetime.fromisoformat(session_data['updated_at'])
        
        return ChatSession(**session_data)

    async def get_chat_session_with_messages(self, session_id: str, user_id: str, limit: int = 50) -> ChatSessionWithMessages:
        """Get chat session with its messages."""
        session = await self.get_chat_session(session_id, user_id)
        messages = await self._get_session_messages(session_id, limit)
        
        # Get document title
        document = await self.document_service.get_document_by_id(session.document_id, user_id)
        
        # Get document summary if available
        try:
            summary = await self.document_service.get_document_summary(session.document_id, user_id)
            summary_text = summary.summary
        except:
            summary_text = None
        
        return ChatSessionWithMessages(
            session=session,
            messages=messages,
            document_title=document.title,
            document_summary=summary_text
        )

    async def get_user_chat_history(self, user_id: str) -> List[ChatSession]:
        """Get all chat sessions for a user."""
        sessions = self.chat_sessions_collection.where('user_id', '==', user_id)\
            .order_by('updated_at', direction='DESCENDING').get()
        
        chat_sessions = []
        for session in sessions:
            session_data = session.to_dict()
            session_data['created_at'] = datetime.fromisoformat(session_data['created_at'])
            session_data['updated_at'] = datetime.fromisoformat(session_data['updated_at'])
            chat_sessions.append(ChatSession(**session_data))
        
        return chat_sessions

    async def delete_chat_session(self, session_id: str, user_id: str) -> bool:
        """Delete a chat session and all its messages."""
        # Verify ownership
        await self.get_chat_session(session_id, user_id)
        
        # Delete all messages in the session
        messages = self.chat_messages_collection.where('chat_session_id', '==', session_id).get()
        for message in messages:
            message.reference.delete()
        
        # Delete the session
        self.chat_sessions_collection.document(session_id).delete()
        
        return True

    async def _add_message(self, session_id: str, role: MessageRole, content: str) -> ChatMessage:
        """Add a message to a chat session."""
        message_id = str(uuid.uuid4())
        
        message_dict = {
            'id': message_id,
            'chat_session_id': session_id,
            'role': role.value,
            'content': content,
            'timestamp': datetime.utcnow()
        }

        # Save to Firestore
        self.chat_messages_collection.document(message_id).set({
            **message_dict,
            'timestamp': message_dict['timestamp'].isoformat()
        })

        # Update session message count
        session_ref = self.chat_sessions_collection.document(session_id)
        session_ref.update({
            'message_count': session_ref.get().to_dict().get('message_count', 0) + 1,
            'updated_at': datetime.utcnow().isoformat()
        })

        return ChatMessage(**message_dict)

    async def _get_session_messages(self, session_id: str, limit: int = 50) -> List[ChatMessage]:
        """Get messages for a chat session."""
        messages = self.chat_messages_collection.where('chat_session_id', '==', session_id)\
            .order_by('timestamp').limit(limit).get()
        
        chat_messages = []
        for message in messages:
            message_data = message.to_dict()
            message_data['timestamp'] = datetime.fromisoformat(message_data['timestamp'])
            chat_messages.append(ChatMessage(**message_data))
        
        return chat_messages

    async def _get_recent_messages(self, session_id: str, limit: int = 10) -> List[dict]:
        """Get recent messages for AI context."""
        messages = self.chat_messages_collection.where('chat_session_id', '==', session_id)\
            .order_by('timestamp', direction='DESCENDING').limit(limit).get()
        
        recent_messages = []
        for message in messages:
            message_data = message.to_dict()
            recent_messages.append({
                'role': message_data['role'],
                'content': message_data['content']
            })
        
        # Reverse to get chronological order
        return list(reversed(recent_messages))

    async def _update_session_timestamp(self, session_id: str):
        """Update session's last activity timestamp."""
        self.chat_sessions_collection.document(session_id).update({
            'updated_at': datetime.utcnow().isoformat()
        })