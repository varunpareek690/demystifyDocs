from fastapi import APIRouter, Depends, HTTPException, File, UploadFile
from models.response import Response
from models.auth import User
from models.document import DocumentUpload
from services.document_service import DocumentService
from api.deps import get_current_user

router = APIRouter()

@router.post("/", response_model=Response)
async def create_summary(
    document_data: DocumentUpload,
    current_user: User = Depends(get_current_user)
):
    """Create summary for a document."""
    try:
        document_service = DocumentService()
        
        # Upload document
        document = await document_service.upload_document(current_user.uid, document_data)
        
        # Generate summary
        summary = await document_service.get_document_summary(document.id, current_user.uid)
        
        return Response(
            success=True,
            message="Document summary generated successfully",
            data={
                "document": document,
                "summary": summary
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{document_id}", response_model=Response)
async def get_summary(
    document_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get summary for a specific document."""
    try:
        document_service = DocumentService()
        summary = await document_service.get_document_summary(document_id, current_user.uid)
        
        return Response(
            success=True,
            message="Summary retrieved successfully",
            data={"summary": summary}
        )
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))
