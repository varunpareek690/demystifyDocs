from typing import List, Optional
from datetime import datetime
from core.firebase_config import get_firestore_client
from models.document import Document, DocumentUpload, DocumentSummary
from services.ai_service import AIService
from utils.exceptions import NotFoundError
import uuid

class DocumentService:
    def __init__(self):
        self.db = get_firestore_client()
        self.documents_collection = self.db.collection('documents')
        self.ai_service = AIService()

    async def upload_document(self, user_id: str, document_data: DocumentUpload) -> Document:
        """Upload and process a document."""
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

    async def get_user_documents(self, user_id: str) -> List[Document]:
        """Get all documents for a user."""
        docs = self.documents_collection.where('user_id', '==', user_id).get()
        
        documents = []
        for doc in docs:
            doc_data = doc.to_dict()
            doc_data['created_at'] = datetime.fromisoformat(doc_data['created_at'])
            doc_data['updated_at'] = datetime.fromisoformat(doc_data['updated_at'])
            documents.append(Document(**doc_data))
        
        return documents

    async def get_document_summary(self, document_id: str, user_id: str) -> DocumentSummary:
        """Generate or retrieve document summary."""
        # Get document
        doc_ref = self.documents_collection.document(document_id)
        doc = doc_ref.get()
        
        if not doc.exists:
            raise NotFoundError("Document not found")
            
        doc_data = doc.to_dict()
        
        # Verify ownership
        if doc_data['user_id'] != user_id:
            raise NotFoundError("Document not found")

        # Check if summary already exists
        summary_ref = self.db.collection('summaries').where('document_id', '==', document_id).limit(1).get()
        
        if summary_ref:
            summary_data = list(summary_ref)[0].to_dict()
            return DocumentSummary(**summary_data)

        # Generate new summary
        ai_result = await self.ai_service.summarize_legal_document(
            doc_data['content'], 
            doc_data['title']
        )

        summary_data = {
            'document_id': document_id,
            'summary': ai_result['summary'],
            'key_points': ai_result['key_points'],
            'complexity_score': ai_result['complexity_score'],
            'created_at': datetime.utcnow()
        }

        # Save summary
        summary_id = str(uuid.uuid4())
        self.db.collection('summaries').document(summary_id).set({
            **summary_data,
            'created_at': summary_data['created_at'].isoformat()
        })

        return DocumentSummary(**summary_data)
