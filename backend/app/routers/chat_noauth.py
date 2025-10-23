from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

router = APIRouter()

class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    query: Optional[str] = None

@router.post("/api/chat/query")
@router.post("/api/chat")
async def chat_no_auth(request: ChatRequest):
    """Chat endpoint without authentication for testing"""
    message = request.message or request.query
    if not message:
        raise HTTPException(status_code=400, detail="No message provided")
    
    return {
        "answer": f"Test response to: {message}. This is a simplified response for testing.",
        "conversation_id": request.conversation_id or "test",
        "context": [],
        "citations": [],
        "quality_metrics": {
            "synthesis_quality": 0.8,
            "citation_precision": 1.0,
            "hallucination_score": 0.0,
            "interpretation_coverage": 0.7
        },
        "processing_time": 0.5,
        "session_id": request.conversation_id or "test",
        "query_id": "test-query",
        "interpretation_links_used": 0,
        "warnings": []
    }
