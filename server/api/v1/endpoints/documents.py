from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Form
from typing import Optional
from models.response import Response
from models.auth import User
from models.document import DocumentUpload, FileUploadResponse, DocumentWithSummary
from services.document_service import DocumentService
from api.deps import get_current_user

router = APIRouter()

@router.post("/upload", response_model=Response)
async def upload_document_file(
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user)
):
    """Upload a document file (PDF, DOCX, TXT)."""
    try:
        document_service = DocumentService()
        
        # Upload and process the file
        result = await document_service.upload_file(
            user_id=current_user.uid, 
            file=file,
            custom_title=title
        )
        
        return Response(
            success=True,
            message="File uploaded successfully",
            data=result
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/text", response_model=Response)
async def upload_document_text(
    document_data: DocumentUpload,
    current_user: User = Depends(get_current_user)
):
    """Upload document as text content."""
    try:
        document_service = DocumentService()
        document = await document_service.upload_document(current_user.uid, document_data)
        
        return Response(
            success=True,
            message="Document uploaded successfully",
            data={"document": document}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/", response_model=Response)
async def get_documents(current_user: User = Depends(get_current_user)):
    """Get user's documents."""
    try:
        document_service = DocumentService()
        documents = await document_service.get_user_documents(current_user.uid)
        
        return Response(
            success=True,
            message="Documents retrieved successfully",
            data={"documents": documents, "count": len(documents)}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{document_id}", response_model=Response)
async def get_document(
    document_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get a specific document."""
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
    current_user: User = Depends(get_current_user)
):
    """Get document with its summary."""
    try:
        document_service = DocumentService()
        
        # Get document
        document = await document_service.get_document_by_id(document_id, current_user.uid)
        
        # Try to get existing summary
        try:
            summary = await document_service.get_document_summary(document_id, current_user.uid)
        except:
            summary = None
        
        result = DocumentWithSummary(document=document, summary=summary)
        
        return Response(
            success=True,
            message="Document and summary retrieved successfully",
            data=result
        )
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.delete("/{document_id}", response_model=Response)
async def delete_document(
    document_id: str,
    current_user: User = Depends(get_current_user)
):
    """Delete a document."""
    try:
        document_service = DocumentService()
        await document_service.delete_document(document_id, current_user.uid)
        
        return Response(
            success=True,
            message="Document deleted successfully",
            data={"document_id": document_id}
        )
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/history", response_model=Response)
async def get_document_history(current_user: User = Depends(get_current_user)):
    """Get document processing history (same as get_documents for now)."""
    try:
        document_service = DocumentService()
        documents = await document_service.get_user_documents(current_user.uid)
        
        # Format as history with additional metadata
        history = [
            {
                "document_id": doc.id,
                "title": doc.title,
                "filename": doc.filename,
                "document_type": doc.document_type,
                "file_type": doc.file_type,
                "file_size": doc.file_size,
                "uploaded_at": doc.created_at,
                "has_summary": False  # Would need to check summaries collection
            }
            for doc in documents
        ]
        
        return Response(
            success=True,
            message="Document history retrieved successfully",
            data={"history": history, "total_documents": len(history)}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))