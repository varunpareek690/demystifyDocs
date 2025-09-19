from typing import List, Optional
from datetime import datetime
from fastapi import UploadFile
from core.firebase_config import get_firestore_client
from models.document import Document, DocumentUpload, DocumentSummary, FileUploadResponse
from services.ai_service import AIService
from utils.exceptions import NotFoundError, FileProcessingError
from utils.file_processor import FileProcessor
from utils.file_storage import LocalFileStorage
import uuid

class DocumentService:
    def __init__(self):
        self.db = get_firestore_client()
        self.documents_collection = self.db.collection('documents')
        self.ai_service = AIService()
        self.file_storage = LocalFileStorage()

    async def upload_document(self, user_id: str, document_data: DocumentUpload) -> Document:
        """Upload and process a document from text."""
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

    async def upload_file(self, user_id: str, file: UploadFile, custom_title: Optional[str] = None) -> FileUploadResponse:
        """Upload and process a file document with local storage."""
        try:
            # Process the uploaded file to extract text
            text_content, file_extension = await FileProcessor.process_uploaded_file(file)
            
            # Save file to local storage
            file_info = await self.file_storage.save_file(file, user_id, custom_title)
            
            # Generate document metadata
            document_id = str(uuid.uuid4())
            title = custom_title or file.filename or f"Document_{document_id[:8]}"
            document_type = FileProcessor.get_document_type(file.filename or "")
            
            # Create document record with file storage info
            doc_dict = {
                'id': document_id,
                'title': title,
                'content': text_content,
                'filename': file_info['original_filename'],
                'stored_filename': file_info['stored_filename'],
                'file_path': file_info['relative_path'],
                'file_size': file_info['file_size'],
                'file_type': file_extension,
                'document_type': document_type,
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

            return FileUploadResponse(
                document_id=document_id,
                filename=file_info['original_filename'],
                title=title,
                file_size=file_info['file_size'],
                file_type=file_extension,
                document_type=document_type,
                stored_filename=file_info['stored_filename'],
                file_path=file_info['relative_path'],
                status="success",
                message="File uploaded and processed successfully"
            )

        except ValueError as e:
            raise FileProcessingError(str(e))
        except Exception as e:
            raise FileProcessingError(f"Unexpected error processing file: {str(e)}")

    async def get_user_documents(self, user_id: str) -> List[Document]:
        """Get all documents for a user."""
        docs = self.documents_collection.where('user_id', '==', user_id).order_by('created_at', direction='DESCENDING').get()
        
        documents = []
        for doc in docs:
            doc_data = doc.to_dict()
            doc_data['created_at'] = datetime.fromisoformat(doc_data['created_at'])
            doc_data['updated_at'] = datetime.fromisoformat(doc_data['updated_at'])
            documents.append(Document(**doc_data))
        
        return documents

    async def get_document_by_id(self, document_id: str, user_id: str) -> Document:
        """Get a specific document by ID."""
        doc_ref = self.documents_collection.document(document_id)
        doc = doc_ref.get()
        
        if not doc.exists:
            raise NotFoundError("Document not found")
            
        doc_data = doc.to_dict()
        
        # Verify ownership
        if doc_data['user_id'] != user_id:
            raise NotFoundError("Document not found")

        doc_data['created_at'] = datetime.fromisoformat(doc_data['created_at'])
        doc_data['updated_at'] = datetime.fromisoformat(doc_data['updated_at'])
        
        return Document(**doc_data)

    async def delete_document(self, document_id: str, user_id: str) -> bool:
        """Delete a document and its associated file."""
        # Get document first to check ownership and get file info
        document = await self.get_document_by_id(document_id, user_id)
        
        # Delete physical file if it exists
        if document.stored_filename:
            self.file_storage.delete_file(user_id, document.stored_filename)
        
        # Delete the document from Firestore
        self.documents_collection.document(document_id).delete()
        
        # Also delete any associated summaries
        summaries = self.db.collection('summaries').where('document_id', '==', document_id).get()
        for summary in summaries:
            summary.reference.delete()
        
        return True

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
            summary_data['created_at'] = datetime.fromisoformat(summary_data['created_at'])
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
            'important_dates': ai_result.get('important_dates', []),
            'obligations': ai_result.get('obligations', []),
            'rights': ai_result.get('rights', []),
            'created_at': datetime.utcnow()
        }

        # Save summary
        summary_id = str(uuid.uuid4())
        self.db.collection('summaries').document(summary_id).set({
            **summary_data,
            'created_at': summary_data['created_at'].isoformat()
        })

        return DocumentSummary(**summary_data)