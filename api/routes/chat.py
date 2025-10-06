"""
Chat and RAG endpoints for maintenance Q&A
"""

import logging
import time
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from api.schemas import (
    ChatRequest, ChatResponse, ChatSource
)
from api.deps import get_database, verify_api_key, get_rag_service
from api.telemetry import structured_logger
# Metrics temporarily disabled: RAG_QUERY_COUNT, RAG_QUERY_DURATION
from rag.retrieve import RAGService

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/chat", response_model=ChatResponse, tags=["chat"])
async def chat_with_rag(
    request: ChatRequest,
    api_key: str = Depends(verify_api_key),
    rag_service: RAGService = Depends(get_rag_service)
):
    """
    Ask questions about maintenance using RAG (Retrieval-Augmented Generation)
    
    - **question**: Your question about maintenance, troubleshooting, or procedures
    - **context**: Optional additional context
    - **include_sources**: Include source documents in response
    - **max_results**: Maximum number of source documents to return
    """
    start_time = time.time()
    
    try:
        # Validate question
        if not request.question.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Question cannot be empty"
            )
        
        # Process the question with RAG service
        result = rag_service.answer_question(
            question=request.question,
            context=request.context,
            max_results=request.max_results,
            include_sources=request.include_sources
        )
        
        # Calculate processing time
        processing_time = time.time() - start_time
        
        # Record metrics (temporarily disabled)
        # TODO: Re-enable metrics once server is stable
        
        # Log structured data
        structured_logger.info(
            "RAG query processed",
            question=request.question[:100],  # Truncate for logging
            processing_time_seconds=processing_time,
            sources_count=len(result.get("sources", [])),
            confidence=result.get("confidence", 0.0)
        )
        
        return ChatResponse(
            answer=result["answer"],
            sources=result.get("sources"),
            confidence=result.get("confidence", 0.8),
            processing_time_seconds=processing_time
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"RAG query error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error processing question"
        )


@router.get("/chat/suggestions", tags=["chat"])
async def get_chat_suggestions(
    category: Optional[str] = Query(None, description="Category of suggestions"),
    limit: int = Query(10, ge=1, le=50, description="Maximum number of suggestions"),
    api_key: str = Depends(verify_api_key)
):
    """
    Get suggested questions for chat
    
    - **category**: Optional category filter
    - **limit**: Maximum number of suggestions
    """
    try:
        # Predefined suggestions based on common maintenance questions
        suggestions = {
            "troubleshooting": [
                "How do I troubleshoot high vibration in motor M01?",
                "What causes temperature spikes in hydraulic systems?",
                "How to diagnose bearing failure symptoms?",
                "What are the signs of pump cavitation?",
                "How to check for misalignment issues?"
            ],
            "maintenance": [
                "What is the maintenance schedule for motor M01?",
                "How often should I lubricate bearings?",
                "What are the inspection procedures for pumps?",
                "How to perform vibration analysis?",
                "What safety procedures for electrical maintenance?"
            ],
            "procedures": [
                "How to safely shut down machine M01?",
                "What is the startup procedure for hydraulic system?",
                "How to calibrate temperature sensors?",
                "What is the lockout/tagout procedure?",
                "How to perform emergency shutdown?"
            ],
            "parts": [
                "What are the part numbers for M01 bearings?",
                "Where to find replacement filters?",
                "What are the specifications for M01 motor?",
                "How to identify correct replacement parts?",
                "What are the lead times for critical parts?"
            ]
        }
        
        if category and category in suggestions:
            selected_suggestions = suggestions[category][:limit]
        else:
            # Return mixed suggestions from all categories
            all_suggestions = []
            for cat_suggestions in suggestions.values():
                all_suggestions.extend(cat_suggestions)
            selected_suggestions = all_suggestions[:limit]
        
        return {
            "suggestions": selected_suggestions,
            "category": category,
            "total_available": sum(len(s) for s in suggestions.values())
        }
        
    except Exception as e:
        logger.error(f"Error getting chat suggestions: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error getting suggestions"
        )


@router.get("/chat/history", tags=["chat"])
async def get_chat_history(
    limit: int = Query(20, ge=1, le=100, description="Maximum number of history items"),
    offset: int = Query(0, ge=0, description="Number of items to skip"),
    api_key: str = Depends(verify_api_key)
):
    """
    Get chat history (mock implementation)
    
    - **limit**: Maximum number of history items
    - **offset**: Number of items to skip
    """
    try:
        # Mock chat history - in production, this would query a database
        mock_history = [
            {
                "id": "chat_001",
                "question": "How do I troubleshoot high vibration?",
                "answer": "High vibration can be caused by misalignment, bearing wear, or imbalance. Check...",
                "timestamp": "2024-01-15T10:30:00Z",
                "confidence": 0.92,
                "sources_count": 3
            },
            {
                "id": "chat_002", 
                "question": "What is the maintenance schedule for M01?",
                "answer": "Motor M01 requires monthly vibration checks, quarterly bearing lubrication...",
                "timestamp": "2024-01-15T09:15:00Z",
                "confidence": 0.88,
                "sources_count": 2
            }
        ]
        
        # Apply pagination
        start_idx = offset
        end_idx = offset + limit
        paginated_history = mock_history[start_idx:end_idx]
        
        return {
            "history": paginated_history,
            "total_count": len(mock_history),
            "has_more": end_idx < len(mock_history)
        }
        
    except Exception as e:
        logger.error(f"Error getting chat history: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error getting chat history"
        )


@router.post("/chat/feedback", tags=["chat"])
async def submit_chat_feedback(
    chat_id: str,
    rating: int = Query(..., ge=1, le=5, description="Rating from 1-5"),
    feedback: Optional[str] = Query(None, description="Optional feedback text"),
    api_key: str = Depends(verify_api_key)
):
    """
    Submit feedback for a chat response
    
    - **chat_id**: Chat session identifier
    - **rating**: Rating from 1-5
    - **feedback**: Optional feedback text
    """
    try:
        # In production, this would store feedback in a database
        structured_logger.info(
            "Chat feedback submitted",
            chat_id=chat_id,
            rating=rating,
            feedback=feedback
        )
        
        return {
            "success": True,
            "message": "Feedback submitted successfully",
            "chat_id": chat_id,
            "rating": rating
        }
        
    except Exception as e:
        logger.error(f"Error submitting feedback: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error submitting feedback"
        )


@router.get("/chat/sources", tags=["chat"])
async def get_available_sources(
    category: Optional[str] = Query(None, description="Filter by category"),
    api_key: str = Depends(verify_api_key),
    rag_service: RAGService = Depends(get_rag_service)
):
    """
    Get available source documents for RAG
    
    - **category**: Optional category filter
    """
    try:
        # Get available sources from RAG service
        sources = rag_service.get_available_sources(category=category)
        
        return {
            "sources": sources,
            "total_count": len(sources),
            "categories": list(set(s.get("category", "unknown") for s in sources))
        }
        
    except Exception as e:
        logger.error(f"Error getting sources: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error getting sources"
        )


@router.post("/chat/search", tags=["chat"])
async def search_documents(
    query: str = Query(..., description="Search query"),
    category: Optional[str] = Query(None, description="Filter by category"),
    limit: int = Query(10, ge=1, le=50, description="Maximum number of results"),
    api_key: str = Depends(verify_api_key),
    rag_service: RAGService = Depends(get_rag_service)
):
    """
    Search documents without generating an answer
    
    - **query**: Search query
    - **category**: Optional category filter
    - **limit**: Maximum number of results
    """
    try:
        # Search documents using RAG service
        results = rag_service.search_documents(
            query=query,
            category=category,
            limit=limit
        )
        
        return {
            "query": query,
            "results": results,
            "total_found": len(results),
            "search_time": time.time()
        }
        
    except Exception as e:
        logger.error(f"Error searching documents: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error searching documents"
        )
