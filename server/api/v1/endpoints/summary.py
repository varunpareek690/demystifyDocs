from fastapi import APIRouter, Depends, HTTPException, Query
from models.response import Response
from models.auth import User
from models.document import DocumentUpload, EnhancedDocumentSummary
from services.document_service import DocumentService
from services.ai_service import VertexAIService
from api.deps import get_current_user

router = APIRouter()

@router.post("/", response_model=Response)
async def create_summary_from_text(
    document_data: DocumentUpload,
    auto_create_chat: bool = Query(True, description="Automatically create chat session"),
    current_user: User = Depends(get_current_user)
):
    """
    Create summary for a document from text content.
    Enhanced to include highlights, key points, and optional chat creation.
    """
    try:
        document_service = DocumentService()
        
        # Upload document
        document = await document_service.upload_document(current_user.uid, document_data)
        
        # Generate enhanced summary
        summary = await document_service.get_document_summary(document.id, current_user.uid)
        
        response_data = {
            "document": document,
            "summary": summary,
            "processing_completed": True
        }
        
        # Optionally create chat session
        if auto_create_chat:
            try:
                from services.chat_service import ChatService
                from models.chat import ChatSessionCreate
                
                chat_service = ChatService()
                session_data = ChatSessionCreate(document_id=document.id)
                chat_session = await chat_service.create_chat_session(current_user.uid, session_data)
                
                # Generate suggested questions
                ai_service = VertexAIService()
                suggested_questions = await ai_service.generate_suggested_questions(
                    document.content, document.title
                )
                
                response_data.update({
                    "chat_session": chat_session,
                    "suggested_questions": suggested_questions,
                    "auto_chat_created": True
                })
                
            except Exception as e:
                response_data["auto_chat_created"] = False
                response_data["chat_creation_error"] = str(e)
        
        return Response(
            success=True,
            message="Document summary generated successfully",
            data=response_data
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{document_id}", response_model=Response)
async def get_summary(
    document_id: str,
    include_highlights: bool = Query(True, description="Include text highlights"),
    include_statistics: bool = Query(False, description="Include processing statistics"),
    current_user: User = Depends(get_current_user)
):
    """
    Get enhanced summary for a specific document.
    Now includes highlights, detailed analysis, and optional statistics.
    """
    try:
        document_service = DocumentService()
        summary = await document_service.get_document_summary(document_id, current_user.uid)
        
        # Get document for additional context if statistics requested
        document = None
        if include_statistics:
            document = await document_service.get_document_by_id(document_id, current_user.uid)
        
        response_data = {"summary": summary}
        
        if include_statistics and document:
            from utils.text_extractor import TextExtractor
            stats = TextExtractor.get_text_statistics(document.content)
            
            response_data["statistics"] = {
                "document_stats": stats,
                "summary_stats": {
                    "key_points_count": len(summary.key_points),
                    "highlights_count": len(summary.highlights),
                    "complexity_score": summary.complexity_score,
                    "obligations_count": len(summary.obligations),
                    "rights_count": len(summary.rights),
                    "risks_count": len(summary.risks),
                    "important_dates_count": len(summary.important_dates)
                }
            }
        
        # Filter highlights if not requested
        if not include_highlights and hasattr(summary, 'highlights'):
            summary_dict = summary.dict()
            summary_dict['highlights'] = []
            response_data["summary"] = summary_dict
        
        return Response(
            success=True,
            message="Summary retrieved successfully",
            data=response_data
        )
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/{document_id}/regenerate", response_model=Response)
async def regenerate_summary(
    document_id: str,
    enhanced_analysis: bool = Query(True, description="Include enhanced analysis features"),
    current_user: User = Depends(get_current_user)
):
    """
    Force regenerate summary for a document with enhanced analysis.
    """
    try:
        document_service = DocumentService()
        
        # Delete existing summary to force regeneration
        summaries = document_service.summaries_collection.where('document_id', '==', document_id).get()
        deleted_count = 0
        for summary in summaries:
            summary.reference.delete()
            deleted_count += 1
        
        # Generate new summary
        summary = await document_service.get_document_summary(document_id, current_user.uid)
        
        # Get document for additional processing if enhanced analysis requested
        processing_info = {}
        if enhanced_analysis:
            document = await document_service.get_document_by_id(document_id, current_user.uid)
            
            # Calculate processing metrics
            from utils.text_extractor import TextExtractor
            stats = TextExtractor.get_text_statistics(document.content)
            
            processing_info = {
                "regeneration_timestamp": summary.created_at.isoformat(),
                "previous_summaries_deleted": deleted_count,
                "document_analysis": stats,
                "ai_processing_notes": {
                    "chunks_processed": 1 if len(document.content) < 3000 else "multiple",
                    "complexity_assessment": "high" if summary.complexity_score > 7 else "moderate" if summary.complexity_score > 4 else "low"
                }
            }
        
        return Response(
            success=True,
            message="Summary regenerated successfully with enhanced analysis",
            data={
                "summary": summary,
                "regeneration_info": processing_info,
                "previous_summaries_deleted": deleted_count
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{document_id}/highlights", response_model=Response)
async def get_summary_highlights(
    document_id: str,
    min_score: float = Query(0.5, ge=0, le=1, description="Minimum relevance score for highlights"),
    limit: int = Query(10, ge=1, le=50, description="Maximum number of highlights"),
    current_user: User = Depends(get_current_user)
):
    """
    Get just the highlights from a document summary for frontend display.
    """
    try:
        document_service = DocumentService()
        summary = await document_service.get_document_summary(document_id, current_user.uid)
        

        highlights = getattr(summary, 'highlights', [])
        
        filtered_highlights = [h for h in highlights if h.get('score', 0) >= min_score]
        
        sorted_highlights = sorted(
            filtered_highlights, 
            key=lambda x: x.get('score', 0), 
            reverse=True
        )[:limit]
        
        formatted_highlights = []
        for highlight in sorted_highlights:
            formatted_highlights.append({
                "text": highlight.get('text', ''),
                "reason": highlight.get('reason', 'Important section'),
                "score": highlight.get('score', 0),
                "page_number": highlight.get('page_number'),
                "position": highlight.get('position'),
                "confidence": "high" if highlight.get('score', 0) > 0.8 else "medium" if highlight.get('score', 0) > 0.6 else "low"
            })
        
        return Response(
            success=True,
            message="Highlights retrieved successfully",
            data={
                "highlights": formatted_highlights,
                "total_highlights": len(highlights),
                "filtered_count": len(formatted_highlights),
                "min_score_filter": min_score,
                "document_id": document_id
            }
        )
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/{document_id}/key-insights", response_model=Response)
async def get_key_insights(
    document_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Get structured key insights from document summary for dashboard display.
    """
    try:
        document_service = DocumentService()
        summary = await document_service.get_document_summary(document_id, current_user.uid)
        document = await document_service.get_document_by_id(document_id, current_user.uid)
        
        insights = {
            "overview": {
                "title": document.title,
                "complexity": {
                    "score": summary.complexity_score,
                    "level": "High" if summary.complexity_score > 7 else "Medium" if summary.complexity_score > 4 else "Low",
                    "description": "Complex legal document" if summary.complexity_score > 7 else "Moderately complex" if summary.complexity_score > 4 else "Straightforward document"
                },
                "summary_preview": summary.summary[:200] + ("..." if len(summary.summary) > 200 else "")
            },
            
            "key_areas": {
                "obligations": {
                    "count": len(summary.obligations),
                    "items": summary.obligations[:5],  # Top 5
                    "has_more": len(summary.obligations) > 5
                },
                "rights": {
                    "count": len(summary.rights),
                    "items": summary.rights[:5],
                    "has_more": len(summary.rights) > 5
                },
                "risks": {
                    "count": len(summary.risks),
                    "items": summary.risks[:5],
                    "has_more": len(summary.risks) > 5
                }
            },
            
            "important_elements": {
                "dates": summary.important_dates[:3],
                "key_points": summary.key_points[:3],
                "top_highlights": [
                    h for h in (getattr(summary, 'highlights', []) or [])
                    if h.get('score', 0) > 0.8
                ][:2]
            },
            
            "actionable_items": []
        }
        
        actionable = []
        if summary.obligations:
            actionable.append({
                "type": "obligation",
                "priority": "high",
                "description": f"Review {len(summary.obligations)} obligations",
                "action": "Check compliance requirements"
            })
        
        if summary.important_dates:
            actionable.append({
                "type": "deadline", 
                "priority": "high",
                "description": f"Track {len(summary.important_dates)} important dates",
                "action": "Set calendar reminders"
            })
        
        if summary.risks:
            actionable.append({
                "type": "risk",
                "priority": "medium",
                "description": f"Assess {len(summary.risks)} potential risks", 
                "action": "Consult with legal advisor if needed"
            })
        
        insights["actionable_items"] = actionable
        
        return Response(
            success=True,
            message="Key insights retrieved successfully",
            data=insights
        )
        
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.delete("/{document_id}/summary", response_model=Response)
async def delete_summary(
    document_id: str,
    current_user: User = Depends(get_current_user)
):
    """Delete summary for a document (will be regenerated on next access)."""
    try:
        document_service = DocumentService()
        
        await document_service.get_document_by_id(document_id, current_user.uid)
        
        summaries = document_service.summaries_collection.where('document_id', '==', document_id).get()
        deleted_count = 0
        for summary in summaries:
            summary.reference.delete()
            deleted_count += 1
        
        return Response(
            success=True,
            message="Summary deleted successfully",
            data={
                "document_id": document_id,
                "summaries_deleted": deleted_count,
                "note": "New summary will be generated on next access"
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))