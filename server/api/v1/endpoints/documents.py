from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Form, Query
from typing import Optional
from models.response import Response
from models.auth import User
from models.document import DocumentUpload, DocumentWithSummary
from services.document_service import DocumentService
from api.deps import get_current_user

router = APIRouter()

@router.post("/upload", response_model=Response)
async def upload_document_file(
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user)
):
    """
    Upload a document file (PDF, DOCX, TXT) with automatic processing.
    
    Now returns:
    - Document metadata
    - AI-generated summary with highlights and key points  
    - Auto-created chat session
    - Suggested questions for the document
    """
    try:
        document_service = DocumentService()
        
        # Upload and process the file (now includes AI processing and chat creation)
        result = await document_service.upload_file(
            user_id=current_user.uid, 
            file=file,
            custom_title=title
        )
        
        return Response(
            success=True,
            message="File uploaded and processed successfully",
            data={
                "document": result["document"],
                "summary": result["summary"], 
                "chat_session": result["chat_session"],
                "suggested_questions": result["suggested_questions"],
                "file_info": result["file_info"]
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/text", response_model=Response)
async def upload_document_text(
    document_data: DocumentUpload,
    auto_create_chat: bool = Query(True, description="Automatically create chat session"),
    current_user: User = Depends(get_current_user)
):
    """
    Upload document as text content with optional auto-chat creation.
    """
    try:
        document_service = DocumentService()
        document = await document_service.upload_document(current_user.uid, document_data)
        
        response_data = {"document": document}
        
        # Optionally create chat session and generate summary
        if auto_create_chat:
            try:
                # Generate summary
                summary = await document_service.get_document_summary(document.id, current_user.uid)
                response_data["summary"] = summary
                
                # Create chat session
                from services.chat_service import ChatService
                from models.chat import ChatSessionCreate
                
                chat_service = ChatService()
                session_data = ChatSessionCreate(document_id=document.id)
                chat_session = await chat_service.create_chat_session(current_user.uid, session_data)
                response_data["chat_session"] = chat_session
                
                # Generate suggested questions
                from services.ai_service import VertexAIService
                ai_service = VertexAIService()
                questions = await ai_service.generate_suggested_questions(document.content, document.title)
                response_data["suggested_questions"] = questions
                
            except Exception:
                pass
        
        return Response(
            success=True,
            message="Document uploaded successfully",
            data=response_data
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/", response_model=Response)
async def get_documents(
    include_summaries: bool = Query(False, description="Include summary data"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of documents"),
    current_user: User = Depends(get_current_user)
):
    """Get user's documents with optional summary information."""
    try:
        document_service = DocumentService()
        documents = await document_service.get_user_documents(current_user.uid)
        
        # Apply limit
        documents = documents[:limit]
        
        response_data = {"documents": documents, "count": len(documents)}
        
        # Optionally include summaries
        if include_summaries:
            documents_with_summaries = []
            for doc in documents:
                try:
                    summary = await document_service.get_document_summary(doc.id, current_user.uid)
                    doc_with_summary = DocumentWithSummary(document=doc, summary=summary)
                except:
                    doc_with_summary = DocumentWithSummary(document=doc, summary=None)
                
                documents_with_summaries.append(doc_with_summary)
            
            response_data["documents_with_summaries"] = documents_with_summaries
        
        return Response(
            success=True,
            message="Documents retrieved successfully",
            data=response_data
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{document_id}", response_model=Response)
async def get_document(
    document_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get a specific document by ID."""
    try:
        document_service = DocumentService()
        document = await document_service.get_document_by_id(document_id, current_user.uid)
        
        return Response(
            success=True,
            message="Document retrieved successfully",
            data={"document": document}
        )
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/{document_id}/with-summary", response_model=Response)
async def get_document_with_summary(
    document_id: str,
    regenerate: bool = Query(False, description="Force regenerate summary"),
    current_user: User = Depends(get_current_user)
):
    """Get document with its AI-generated summary and analysis."""
    try:
        document_service = DocumentService()
        
        # Get document
        document = await document_service.get_document_by_id(document_id, current_user.uid)
        
        # Get or generate summary
        if regenerate:
            # Force regeneration by deleting existing summary first
            try:
                # Delete existing summaries
                summaries = document_service.summaries_collection.where('document_id', '==', document_id).get()
                for summary in summaries:
                    summary.reference.delete()
            except:
                pass
        
        try:
            summary = await document_service.get_document_summary(document_id, current_user.uid)
        except:
            summary = None
        
        # Get associated chat sessions
        chat_sessions = document_service.chat_sessions_collection.where(
            'document_id', '==', document_id
        ).where('user_id', '==', current_user.uid).get()
        
        sessions_data = []
        for session in chat_sessions:
            session_data = session.to_dict()
            session_data['created_at'] = session_data['created_at']
            session_data['updated_at'] = session_data['updated_at']
            sessions_data.append(session_data)
        
        result = {
            "document": document,
            "summary": summary,
            "chat_sessions": sessions_data,
            "has_chat_sessions": len(sessions_data) > 0
        }
        
        return Response(
            success=True,
            message="Document and summary retrieved successfully",
            data=result
        )
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/{document_id}/download", response_model=Response)
async def get_document_download_url(
    document_id: str,
    expiration_minutes: int = Query(60, ge=5, le=1440, description="URL expiration in minutes"),
    current_user: User = Depends(get_current_user)
):
    """Generate a signed URL for downloading the original document file."""
    try:
        document_service = DocumentService()
        document = await document_service.get_document_by_id(document_id, current_user.uid)
        
        if not hasattr(document, 'blob_path') or not document.blob_path:
            raise HTTPException(status_code=404, detail="Original file not available for download")
        
        # Generate signed URL
        signed_url = await document_service.file_storage.generate_signed_url(
            document.blob_path, 
            current_user.uid,
            expiration_minutes
        )
        
        return Response(
            success=True,
            message="Download URL generated successfully",
            data={
                "download_url": signed_url,
                "filename": document.filename,
                "file_size": document.file_size,
                "expires_in_minutes": expiration_minutes
            }
        )
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/{document_id}/regenerate-summary", response_model=Response)
async def regenerate_document_summary(
    document_id: str,
    current_user: User = Depends(get_current_user)
):
    """Force regenerate AI summary for a document."""
    try:
        document_service = DocumentService()
        
        # Delete existing summary
        summaries = document_service.summaries_collection.where('document_id', '==', document_id).get()
        for summary in summaries:
            summary.reference.delete()
        
        # Generate new summary
        summary = await document_service.get_document_summary(document_id, current_user.uid)
        
        return Response(
            success=True,
            message="Summary regenerated successfully",
            data={"summary": summary}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{document_id}", response_model=Response)
async def delete_document(
    document_id: str,
    current_user: User = Depends(get_current_user)
):
    """Delete a document, its GCS file, summaries, and associated chat sessions."""
    try:
        document_service = DocumentService()
        await document_service.delete_document(document_id, current_user.uid)
        
        return Response(
            success=True,
            message="Document and all associated data deleted successfully",
            data={"document_id": document_id}
        )
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/history/detailed", response_model=Response)
async def get_detailed_document_history(
    include_summaries: bool = Query(False, description="Include summary information"),
    include_chat_info: bool = Query(True, description="Include chat session counts"),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user)
):
    """Get detailed document processing history with enhanced metadata."""
    try:
        document_service = DocumentService()
        documents = await document_service.get_user_documents(current_user.uid)
        
        history = []
        for doc in documents[:limit]:
            doc_history = {
                "document_id": doc.id,
                "title": doc.title,
                "filename": getattr(doc, 'filename', None),
                "document_type": doc.document_type,
                "file_type": getattr(doc, 'file_type', None),
                "file_size": getattr(doc, 'file_size', None),
                "uploaded_at": doc.created_at,
                "updated_at": doc.updated_at,
                "has_gcs_file": hasattr(doc, 'blob_path') and bool(getattr(doc, 'blob_path', None))
            }
            
            # Add summary info if requested
            if include_summaries:
                try:
                    summary = await document_service.get_document_summary(doc.id, current_user.uid)
                    doc_history["summary"] = {
                        "summary": summary.summary[:200] + "..." if len(summary.summary) > 200 else summary.summary,
                        "complexity_score": summary.complexity_score,
                        "key_points_count": len(summary.key_points),
                        "has_highlights": len(getattr(summary, 'highlights', [])) > 0
                    }
                except:
                    doc_history["summary"] = None
            
            # Add chat session info if requested
            if include_chat_info:
                try:
                    sessions = document_service.chat_sessions_collection.where(
                        'document_id', '==', doc.id
                    ).where('user_id', '==', current_user.uid).get()
                    
                    total_messages = sum(session.to_dict().get('message_count', 0) for session in sessions)
                    
                    doc_history["chat_info"] = {
                        "session_count": len(sessions),
                        "total_messages": total_messages,
                        "has_active_chats": len(sessions) > 0
                    }
                except:
                    doc_history["chat_info"] = {"session_count": 0, "total_messages": 0, "has_active_chats": False}
            
            history.append(doc_history)
        
        return Response(
            success=True,
            message="Detailed document history retrieved successfully",
            data={
                "history": history, 
                "total_documents": len(history),
                "showing_limit": limit
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
