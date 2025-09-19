from fastapi import APIRouter
from api.v1.endpoints import auth, summary, chat, documents

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(summary.router, prefix="/summary", tags=["summary"])
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])
api_router.include_router(documents.router, prefix="/documents", tags=["documents"])
