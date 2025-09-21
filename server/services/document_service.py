from typing import List, Optional, Dict, Any
from datetime import datetime
from fastapi import UploadFile
from core.firebase_config import get_firestore_client
from models.document import Document, DocumentUpload, DocumentSummary, FileUploadResponse
from models.chat import ChatSession
from services.ai_service import VertexAIService
from services.file_storage_gcs import GCSFileStorage
from utils.exceptions import NotFoundError, FileProcessingError, ServiceUnavailableError
from utils.text_extractor import TextExtractor
import uuid

class DocumentService:
    """Document management service with GCS storage and auto-chat creation."""
    
    def __init__(self):
        self.db = get_firestore_client()
        self.documents_collection = self.db.collection('documents')
        self.summaries_collection = self.db.collection('summaries')
        self.chat_sessions_collection = self.db.collection('chat_sessions')
        self.ai_service = VertexAIService()
        self.file_storage = GCSFileStorage()
        self.text_extractor = TextExtractor()

    async def upload_document(self, user_id: str, document_data: DocumentUpload) -> Document:
        """Upload and process a document from text content."""
        document_id = str(uuid.uuid4())
        
        # Create document record
        doc_dict = {
            'id': document_id,
            'title': document_data.title,
            'content': document_data.content,
            'document_type': document_data.document_type,
            'user_id': user_id,
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }

        # Save to Firestore
        self.documents_collection.document(document_id).set({
            **doc_dict,
            'created_at': doc_dict['created_at'].isoformat(),
            'updated_at': doc_dict['updated_at'].isoformat()
        })

        return Document(**doc_dict)

    async def upload_file(self, user_id: str, file: UploadFile, custom_title: Optional[str] = None) -> Dict[str, Any]:
        """
        Upload and process a file with GCS storage and automatic chat session creation.
        
        Returns:
            Dict containing document info, summary, session data, and suggested questions
        """
        try:
            
            file_info = await self.file_storage.save_file(file, user_id, custom_title)
            
            await file.seek(0)
            text_content = await self.text_extractor.extract_text(file)
            
            if not text_content.strip():
                raise FileProcessingError("No text content could be extracted from the file")
            
            document_id = str(uuid.uuid4())
            title = custom_title or file.filename or f"Document_{document_id[:8]}"
            document_type = self._get_document_type(file.filename or "")
            
            doc_dict = {
                'id': document_id,
                'title': title,
                'content': text_content,
                'filename': file_info['original_filename'],
                'blob_path': file_info['blob_path'],
                'file_size': file_info['file_size'],
                'file_type': self._get_file_extension(file_info['original_filename']),
                'content_type': file_info['content_type'],
                'document_type': document_type,
                'user_id': user_id,
                'gcs_url': file_info['gcs_url'],
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow()
            }

            self.documents_collection.document(document_id).set({
                **doc_dict,
                'created_at': doc_dict['created_at'].isoformat(),
                'updated_at': doc_dict['updated_at'].isoformat()
            })
            
            try:
                summary_data = await self.ai_service.summarize_document(text_content, title)
                
                summary_dict = {
                    'document_id': document_id,
                    'summary': summary_data['summary'],
                    'key_points': summary_data['key_points'],
                    'highlights': summary_data['highlights'],
                    'complexity_score': summary_data['complexity_score'],
                    'important_dates': summary_data.get('important_dates', []),
                    'obligations': summary_data.get('obligations', []),
                    'rights': summary_data.get('rights', []),
                    'risks': summary_data.get('risks', []),
                    'created_at': datetime.utcnow()
                }
                
                summary_id = str(uuid.uuid4())
                self.summaries_collection.document(summary_id).set({
                    **summary_dict,
                    'created_at': summary_dict['created_at'].isoformat()
                })
                
            except Exception as e:
                summary_data = {
                    'summary': f"Document '{title}' has been uploaded and processed successfully.",
                    'key_points': ["Document uploaded successfully", "Text content extracted"],
                    'highlights': [],
                    'complexity_score': 5,
                    'important_dates': [],
                    'obligations': [],
                    'rights': [],
                    'risks': []
                }
                
                summary_dict = {
                    'document_id': document_id,
                    **summary_data,
                    'created_at': datetime.utcnow()
                }
            
            try:
                session_id = str(uuid.uuid4())
                chat_title = f"Discussion about {title}"
                
                session_dict = {
                    'id': session_id,
                    'user_id': user_id,
                    'document_id': document_id,
                    'title': chat_title,
                    'created_at': datetime.utcnow(),
                    'updated_at': datetime.utcnow(),
                    'message_count': 1,
                    'is_active': True
                }

                self.chat_sessions_collection.document(session_id).set({
                    **session_dict,
                    'created_at': session_dict['created_at'].isoformat(),
                    'updated_at': session_dict['updated_at'].isoformat()
                })
                
                initial_message = f"""I've analyzed your document "{title}" and here's what I found:

**Summary:**
{summary_data['summary']}

**Key Points:**
{chr(10).join(f'• {point}' for point in summary_data['key_points'])}

I'm ready to answer any questions you have about this document. You can ask me about specific sections, legal implications, your obligations, or anything else you'd like to understand better."""

                from services.chat_service import ChatService
                chat_service = ChatService()
                await chat_service._add_message(session_id, "ai", initial_message)
                                
            except Exception:
                session_dict = None
            
            try:
                suggested_questions = await self.ai_service.generate_suggested_questions(text_content, title)
            except Exception as e:
                suggested_questions = [
                    "What are the main points of this document?",
                    "What obligations do I have under this document?",
                    "Are there any important deadlines?",
                    "What should I be most concerned about?",
                    "What are my rights according to this document?"
                ]
            
            return {
                'document': Document(**doc_dict),
                'summary': DocumentSummary(**summary_dict),
                'chat_session': ChatSession(**session_dict) if session_dict else None,
                'suggested_questions': suggested_questions,
                'file_info': {
                    'blob_path': file_info['blob_path'],
                    'gcs_url': file_info['gcs_url'],
                    'file_size': file_info['file_size'],
                    'content_type': file_info['content_type']
                }
            }
            
        except FileProcessingError:
            raise
        except Exception as e:
            raise FileProcessingError(f"File processing failed: {str(e)}")

    async def get_user_documents(self, user_id: str) -> List[Document]:
        """Get all documents for a user."""
        try:
            docs = self.documents_collection.where('user_id', '==', user_id)\
                .order_by('created_at', direction='DESCENDING').get()
            
            documents = []
            for doc in docs:
                doc_data = doc.to_dict()
                doc_data['created_at'] = datetime.fromisoformat(doc_data['created_at'])
                doc_data['updated_at'] = datetime.fromisoformat(doc_data['updated_at'])
                documents.append(Document(**doc_data))
            
            return documents
            
        except Exception as e:
            raise ServiceUnavailableError(f"Failed to retrieve documents: {str(e)}")

    async def get_document_by_id(self, document_id: str, user_id: str) -> Document:
        """Get a specific document by ID."""
        try:
            doc_ref = self.documents_collection.document(document_id)
            doc = doc_ref.get()
            
            if not doc.exists:
                raise NotFoundError("Document not found")
                
            doc_data = doc.to_dict()
            
            if doc_data['user_id'] != user_id:
                raise NotFoundError("Document not found")

            doc_data['created_at'] = datetime.fromisoformat(doc_data['created_at'])
            doc_data['updated_at'] = datetime.fromisoformat(doc_data['updated_at'])
            
            return Document(**doc_data)
            
        except NotFoundError:
            raise
        except Exception as e:
            raise ServiceUnavailableError(f"Failed to retrieve document: {str(e)}")

    async def delete_document(self, document_id: str, user_id: str) -> bool:
        """Delete a document and its associated GCS file."""
        try:
            document = await self.get_document_by_id(document_id, user_id)
            
            if hasattr(document, 'blob_path') and document.blob_path:
                try:
                    await self.file_storage.delete_file(document.blob_path, user_id)
                except Exception:
                    pass            
            self.documents_collection.document(document_id).delete()
            
            summaries = self.summaries_collection.where('document_id', '==', document_id).get()
            for summary in summaries:
                summary.reference.delete()
            
            sessions = self.chat_sessions_collection.where('document_id', '==', document_id).get()
            for session in sessions:
                session_id = session.id
                messages = self.db.collection('chat_messages').where('chat_session_id', '==', session_id).get()
                for message in messages:
                    message.reference.delete()
                session.reference.delete()
            
            return True
            
        except NotFoundError:
            raise
        except Exception as e:
            raise ServiceUnavailableError(f"Failed to delete document: {str(e)}")

    async def get_document_summary(self, document_id: str, user_id: str) -> DocumentSummary:
        """Get or generate document summary."""
        try:
            # Verify document ownership
            await self.get_document_by_id(document_id, user_id)
            
            # Check if summary already exists
            summary_query = self.summaries_collection.where('document_id', '==', document_id).limit(1).get()
            
            if summary_query:
                summary_data = list(summary_query)[0].to_dict()
                summary_data['created_at'] = datetime.fromisoformat(summary_data['created_at'])
                return DocumentSummary(**summary_data)
            
            # Generate new summary if none exists
            document = await self.get_document_by_id(document_id, user_id)
            
            ai_result = await self.ai_service.summarize_document(
                document.content, 
                document.title
            )

            summary_data = {
                'document_id': document_id,
                'summary': ai_result['summary'],
                'key_points': ai_result['key_points'],
                'highlights': ai_result.get('highlights', []),
                'complexity_score': ai_result['complexity_score'],
                'important_dates': ai_result.get('important_dates', []),
                'obligations': ai_result.get('obligations', []),
                'rights': ai_result.get('rights', []),
                'risks': ai_result.get('risks', []),
                'created_at': datetime.utcnow()
            }

            # Save summary
            summary_id = str(uuid.uuid4())
            self.summaries_collection.document(summary_id).set({
                **summary_data,
                'created_at': summary_data['created_at'].isoformat()
            })

            return DocumentSummary(**summary_data)
            
        except NotFoundError:
            raise
        except Exception as e:
            raise ServiceUnavailableError(f"Failed to generate summary: {str(e)}")

    async def get_document_with_file_content(self, document_id: str, user_id: str) -> bytes:
        """Get original file content from GCS."""
        try:
            document = await self.get_document_by_id(document_id, user_id)
            
            if not hasattr(document, 'blob_path') or not document.blob_path:
                raise NotFoundError("Original file not available")
            
            return await self.file_storage.get_file_content(document.blob_path, user_id)
            
        except NotFoundError:
            raise
        except Exception as e:
            raise ServiceUnavailableError(f"Failed to retrieve file: {str(e)}")

    def _get_document_type(self, filename: str) -> str:
        """Determine document type from filename."""
        filename_lower = filename.lower()
        if any(keyword in filename_lower for keyword in ['contract', 'agreement', 'terms']):
            return 'contract'
        elif any(keyword in filename_lower for keyword in ['policy', 'procedure', 'manual']):
            return 'policy'
        elif any(keyword in filename_lower for keyword in ['report', 'analysis', 'summary']):
            return 'report'
        else:
            return 'legal'

    def _get_file_extension(self, filename: str) -> str:
        """Extract file extension from filename."""
        if '.' in filename:
            return '.' + filename.rsplit('.', 1)[1].lower()
        return ''
