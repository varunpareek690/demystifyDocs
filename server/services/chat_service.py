from typing import List
from datetime import datetime
from core.firebase_config import get_firestore_client
from models.chat import (
    ChatSession, ChatMessage, MessageRole, ChatSessionCreate, 
    SendMessageRequest, ChatSessionWithMessages
)
from services.document_service import DocumentService
from services.ai_service import VertexAIService
from utils.exceptions import NotFoundError, ServiceUnavailableError
import uuid

class ChatService:
    """Chat service with Vertex AI integration."""
    
    def __init__(self):
        self.db = get_firestore_client()
        self.chat_sessions_collection = self.db.collection('chat_sessions')
        self.chat_messages_collection = self.db.collection('chat_messages')
        self.ai_service = VertexAIService()

    async def create_chat_session(self, user_id: str, session_data: ChatSessionCreate) -> ChatSession:
        """Create a new chat session with a document."""
        try:
            # Import here to avoid circular import
            from services.document_service import DocumentService
            document_service = DocumentService()
            
            # Verify document exists and belongs to user
            document = await document_service.get_document_by_id(session_data.document_id, user_id)
            
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

            self.chat_sessions_collection.document(session_id).set({
                **session_dict,
                'created_at': session_dict['created_at'].isoformat(),
                'updated_at': session_dict['updated_at'].isoformat()
            })

            try:
                summary = await document_service.get_document_summary(session_data.document_id, user_id)
                system_content = f"""I've analyzed the document "{document.title}". Here's what I found:

**Summary:**
{summary.summary}

**Key Points:**
{chr(10).join(f'• {point}' for point in summary.key_points)}

You can ask me any questions about this document, and I'll help you understand its contents, implications, and answer any legal questions you might have."""
            except Exception as e:
                system_content = f"""I have the document "{document.title}" available for discussion. You can ask me any questions about its contents, and I'll help you understand its implications and answer any legal questions you might have."""

            await self._add_message(session_id, MessageRole.AI, system_content)
            
            return ChatSession(**session_dict)
            
        except Exception as e:
            raise ServiceUnavailableError(f"Could not create chat session: {str(e)}")

    async def send_message(self, session_id: str, user_id: str, message_request: SendMessageRequest) -> tuple[ChatMessage, ChatMessage]:
        """Send a message and get AI response using Vertex AI."""
        try:
            # Verify session exists and belongs to user
            session = await self.get_chat_session(session_id, user_id)
            
            # Add user message
            user_message = await self._add_message(session_id, MessageRole.USER, message_request.message)
            
            # Get document context
            from services.document_service import DocumentService
            document_service = DocumentService()
            document = await document_service.get_document_by_id(session.document_id, user_id)
            
            # Get recent messages for context
            recent_messages = await self._get_recent_messages(session_id, limit=10)
            
            # Generate AI response using Vertex AI
            ai_response_content = await self.ai_service.chat_with_document(
                document_content=document.content,
                document_title=document.title,
                user_message=message_request.message,
                chat_history=recent_messages
            )
            
            ai_message = await self._add_message(session_id, MessageRole.AI, ai_response_content)            
            await self._update_session_timestamp(session_id)
            
            return user_message, ai_message
            
        except NotFoundError:
            raise
        except Exception as e:
            raise ServiceUnavailableError(f"Could not process message: {str(e)}")

    async def get_chat_session(self, session_id: str, user_id: str) -> ChatSession:
        """Get a specific chat session."""
        try:
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
            
        except NotFoundError:
            raise
        except Exception as e:
            raise ServiceUnavailableError(f"Could not retrieve chat session: {str(e)}")

    async def get_chat_session_with_messages(self, session_id: str, user_id: str, limit: int = 50) -> ChatSessionWithMessages:
        """Get chat session with its messages."""
        try:
            session = await self.get_chat_session(session_id, user_id)
            messages = await self._get_session_messages(session_id, limit)
            
            from services.document_service import DocumentService
            document_service = DocumentService()
            document = await document_service.get_document_by_id(session.document_id, user_id)
            
            # Get document summary if available
            try:
                summary = await document_service.get_document_summary(session.document_id, user_id)
                summary_text = summary.summary
            except:
                summary_text = None
            
            return ChatSessionWithMessages(
                session=session,
                messages=messages,
                document_title=document.title,
                document_summary=summary_text
            )
            
        except NotFoundError:
            raise
        except Exception as e:
            raise ServiceUnavailableError(f"Could not retrieve chat session: {str(e)}")

    async def get_user_chat_history(self, user_id: str) -> List[ChatSession]:
        """Get all chat sessions for a user."""
        try:
            sessions = self.chat_sessions_collection.where('user_id', '==', user_id)\
                .order_by('updated_at', direction='DESCENDING').get()
            
            chat_sessions = []
            for session in sessions:
                session_data = session.to_dict()
                session_data['created_at'] = datetime.fromisoformat(session_data['created_at'])
                session_data['updated_at'] = datetime.fromisoformat(session_data['updated_at'])
                chat_sessions.append(ChatSession(**session_data))
            
            return chat_sessions
            
        except Exception as e:
            raise ServiceUnavailableError(f"Could not retrieve chat history: {str(e)}")

    async def delete_chat_session(self, session_id: str, user_id: str) -> bool:
        """Delete a chat session and all its messages."""
        try:
            await self.get_chat_session(session_id, user_id)
            
            messages = self.chat_messages_collection.where('chat_session_id', '==', session_id).get()
            for message in messages:
                message.reference.delete()
            
            self.chat_sessions_collection.document(session_id).delete()            
            return True
            
        except NotFoundError:
            raise
        except Exception as e:
            raise ServiceUnavailableError(f"Could not delete chat session: {str(e)}")

    async def _add_message(self, session_id: str, role: MessageRole, content: str) -> ChatMessage:
        """Add a message to a chat session."""
        try:
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
            session_doc = session_ref.get()
            current_count = session_doc.to_dict().get('message_count', 0) if session_doc.exists else 0
            
            session_ref.update({
                'message_count': current_count + 1,
                'updated_at': datetime.utcnow().isoformat()
            })

            return ChatMessage(**message_dict)
            
        except Exception as e:
            raise ServiceUnavailableError(f"Could not save message: {str(e)}")

    async def _get_session_messages(self, session_id: str, limit: int = 50) -> List[ChatMessage]:
        """Get messages for a chat session."""
        try:
            messages = self.chat_messages_collection.where('chat_session_id', '==', session_id)\
                .order_by('timestamp').limit(limit).get()
            
            chat_messages = []
            for message in messages:
                message_data = message.to_dict()
                message_data['timestamp'] = datetime.fromisoformat(message_data['timestamp'])
                chat_messages.append(ChatMessage(**message_data))
            
            return chat_messages
            
        except Exception:
            return []

    async def _get_recent_messages(self, session_id: str, limit: int = 10) -> List[dict]:
        """Get recent messages for AI context."""
        try:
            messages = self.chat_messages_collection.where('chat_session_id', '==', session_id)\
                .order_by('timestamp', direction='DESCENDING').limit(limit).get()
            
            recent_messages = []
            for message in messages:
                message_data = message.to_dict()
                recent_messages.append({
                    'role': message_data['role'],
                    'content': message_data['content']
                })
            
            return list(reversed(recent_messages))
            
        except Exception:
            return []

    async def _update_session_timestamp(self, session_id: str):
        """Update session's last activity timestamp."""
        try:
            self.chat_sessions_collection.document(session_id).update({
                'updated_at': datetime.utcnow().isoformat()
            })
        except Exception:
            pass

    async def get_session_suggested_questions(self, session_id: str, user_id: str) -> List[str]:
        """Get suggested questions for a chat session based on the document."""
        try:
            session = await self.get_chat_session(session_id, user_id)
            
            from services.document_service import DocumentService
            document_service = DocumentService()
            document = await document_service.get_document_by_id(session.document_id, user_id)
            
            questions = await self.ai_service.generate_suggested_questions(
                document.content, 
                document.title
            )
            
            return questions
            
        except Exception:
            return [
                "What are the main points of this document?",
                "What obligations do I have under this document?",
                "Are there any important deadlines?",
                "What should I be most concerned about?",
                "What are my rights according to this document?"
            ]