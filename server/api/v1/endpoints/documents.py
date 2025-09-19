from fastapi import APIRouter, Depends, HTTPException, File, UploadFile
from models.response import Response
from models.auth import User
from models.document import DocumentUpload
from services.document_service import DocumentService
from api.deps import get_current_user

router = APIRouter()

@router.post("/upload", response_model=Response)
async def upload_document(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """Upload document file (placeholder)."""
    return Response(
        success=True,
        message="File upload endpoint - Coming soon",
        data={
            "filename": file.filename,
            "content_type": file.content_type,
            "user_id": current_user.uid,
            "status": "placeholder"
        }
    )

@router.get("/", response_model=Response)
async def get_documents(current_user: User = Depends(get_current_user)):
    """Get user's documents."""
    try:
        document_service = DocumentService()
        documents = await document_service.get_user_documents(current_user.uid)
        
        return Response(
            success=True,
            message="Documents retrieved successfully",
            data={"documents": documents}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    