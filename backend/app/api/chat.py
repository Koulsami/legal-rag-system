"""
Chat API endpoints for Legal RAG queries
Handles user queries, retrieval, and generation
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging
import time
import uuid

from app.core.dependencies import get_current_user, get_db
from app.services.retrieval import retrieval_service
from app.services.generation import generation_service
from app.services.interpretation_links import interpretation_link_service
from app.services.validator import validation_service
from app.database.models import User, QueryLog
from sqlalchemy.orm import Session

router = APIRouter()
logger = logging.getLogger(__name__)


# Request/Response Models
class QueryRequest(BaseModel):
    """User query request"""
    query: str = Field(..., min_length=10, max_length=1000)
    session_id: Optional[str] = None
    include_interpretive_cases: bool = True
    max_results: int = Field(default=10, ge=5, le=20)
    enable_synthesis: bool = True


class ContextDocument(BaseModel):
    """Retrieved context document"""
    doc_id: str
    doc_type: str  # "statute" | "case"
    title: str
    text: str
    citation: str
    score: float
    is_interpretive: bool = False
    interprets_statute_id: Optional[str] = None
    interpretation_type: Optional[str] = None


class QueryResponse(BaseModel):
    """Response to user query"""
    answer: str
    context: List[ContextDocument]
    citations: List[str]
    quality_metrics: Dict[str, float]
    processing_time: float
    session_id: str
    query_id: str
    interpretation_links_used: int
    warnings: List[str] = []


class QueryHistory(BaseModel):
    """User's query history"""
    query_id: str
    query_text: str
    timestamp: datetime
    processing_time: float
    quality_score: float


class ExportRequest(BaseModel):
    """Export conversation request"""
    session_id: str
    format: str = Field(default="pdf", pattern="^(pdf|markdown|json)$")
    include_context: bool = True


# === MAIN CHAT ENDPOINT ===

@router.post("/query", response_model=QueryResponse)
async def chat_query(
    request: QueryRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Main chat endpoint for legal queries
    
    This integrates:
    1. Hybrid retrieval (BM25 + Dense + LePaRD)
    2. Interpretation link boosting
    3. Synthesis prompt generation
    4. Validation
    """
    start_time = time.time()
    query_id = str(uuid.uuid4())
    session_id = request.session_id or str(uuid.uuid4())
    
    logger.info(f"Query {query_id}: '{request.query}' from user {current_user.id}")
    
    try:
        # Step 1: Retrieve relevant documents (statutes + cases)
        logger.info(f"Query {query_id}: Starting retrieval")
        retrieval_results = await retrieval_service.hybrid_retrieve(
            query=request.query,
            top_k=request.max_results,
            enable_lepard=True
        )
        
        # Step 2: Apply interpretation link boosting
        if request.include_interpretive_cases:
            logger.info(f"Query {query_id}: Applying interpretation links")
            retrieval_results = await interpretation_link_service.boost_with_interpretive_cases(
                query_results=retrieval_results,
                max_interpretive_per_statute=3
            )
        
        # Step 3: Format context for generation
        formatted_context = _format_context_for_generation(retrieval_results)
        
        # Step 4: Generate synthesis answer
        logger.info(f"Query {query_id}: Generating answer")
        answer, citations = await generation_service.generate_statutory_interpretation(
            query=request.query,
            context=formatted_context,
            enable_synthesis=request.enable_synthesis
        )
        
        # Step 5: Validate response
        logger.info(f"Query {query_id}: Validating response")
        validation_result = await validation_service.validate_response(
            query=request.query,
            answer=answer,
            citations=citations,
            context=retrieval_results
        )
        
        processing_time = time.time() - start_time
        
        # Prepare response
        context_docs = [
            ContextDocument(
                doc_id=doc["doc_id"],
                doc_type=doc["doc_type"],
                title=doc["title"],
                text=doc["text"],
                citation=doc["citation"],
                score=doc["score"],
                is_interpretive=doc.get("is_interpretive", False),
                interprets_statute_id=doc.get("interprets_statute_id"),
                interpretation_type=doc.get("interpretation_type")
            )
            for doc in retrieval_results
        ]
        
        response = QueryResponse(
            answer=answer,
            context=context_docs,
            citations=citations,
            quality_metrics={
                "synthesis_quality": validation_result.quality_score,
                "citation_precision": validation_result.citation_precision,
                "hallucination_score": validation_result.hallucination_score,
                "interpretation_coverage": validation_result.interpretation_coverage
            },
            processing_time=processing_time,
            session_id=session_id,
            query_id=query_id,
            interpretation_links_used=sum(1 for doc in retrieval_results if doc.get("is_interpretive")),
            warnings=validation_result.warnings
        )
        
        # Log query in background
        background_tasks.add_task(
            _log_query,
            db=db,
            user_id=current_user.id,
            query_id=query_id,
            session_id=session_id,
            query_text=request.query,
            response=response
        )
        
        logger.info(
            f"Query {query_id} completed in {processing_time:.2f}s - "
            f"Quality: {validation_result.quality_score:.2f}"
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Query {query_id} failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Query processing failed: {str(e)}"
        )


def _format_context_for_generation(retrieval_results: List[Dict[str, Any]]) -> str:
    """Format retrieved documents for LLM context"""
    formatted = []
    
    # Group by type
    statutes = [doc for doc in retrieval_results if doc["doc_type"] == "statute"]
    cases = [doc for doc in retrieval_results if doc["doc_type"] == "case"]
    interpretive_cases = [doc for doc in cases if doc.get("is_interpretive")]
    other_cases = [doc for doc in cases if not doc.get("is_interpretive")]
    
    # Format statutes first
    if statutes:
        formatted.append("=== RELEVANT STATUTES ===\n")
        for i, doc in enumerate(statutes, 1):
            formatted.append(f"[STATUTE {i}] {doc['citation']}")
            formatted.append(f"Title: {doc['title']}")
            formatted.append(f"Text: {doc['text']}\n")
    
    # Then interpretive cases with markers
    if interpretive_cases:
        formatted.append("\n=== INTERPRETIVE CASE LAW ===")
        formatted.append("(These cases specifically interpret the above statutes)\n")
        for i, doc in enumerate(interpretive_cases, 1):
            formatted.append(f"[INTERPRETS STATUTE] [CASE {i}] {doc['citation']}")
            formatted.append(f"Interpretation Type: {doc.get('interpretation_type', 'CLARIFY')}")
            formatted.append(f"Authority: {doc.get('authority_level', 'PERSUASIVE')}")
            formatted.append(f"Interprets: {doc.get('interprets_statute_id')}")
            formatted.append(f"Text: {doc['text']}\n")
    
    # Finally other relevant cases
    if other_cases:
        formatted.append("\n=== OTHER RELEVANT CASE LAW ===\n")
        for i, doc in enumerate(other_cases, 1):
            formatted.append(f"[CASE {len(interpretive_cases) + i}] {doc['citation']}")
            formatted.append(f"Text: {doc['text']}\n")
    
    return "\n".join(formatted)


def _log_query(
    db: Session,
    user_id: int,
    query_id: str,
    session_id: str,
    query_text: str,
    response: QueryResponse
):
    """Log query to database"""
    try:
        log_entry = QueryLog(
            query_id=query_id,
            session_id=session_id,
            user_id=user_id,
            query_text=query_text,
            answer=response.answer,
            processing_time=response.processing_time,
            quality_score=response.quality_metrics["synthesis_quality"],
            interpretation_links_used=response.interpretation_links_used,
            context_documents=len(response.context)
        )
        db.add(log_entry)
        db.commit()
    except Exception as e:
        logger.error(f"Failed to log query {query_id}: {e}")
        db.rollback()


# === ADDITIONAL ENDPOINTS ===

@router.get("/history", response_model=List[QueryHistory])
async def get_query_history(
    limit: int = Query(default=50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's query history"""
    logs = db.query(QueryLog)\
        .filter(QueryLog.user_id == current_user.id)\
        .order_by(QueryLog.created_at.desc())\
        .limit(limit)\
        .all()
    
    return [
        QueryHistory(
            query_id=log.query_id,
            query_text=log.query_text,
            timestamp=log.created_at,
            processing_time=log.processing_time,
            quality_score=log.quality_score
        )
        for log in logs
    ]


@router.post("/export")
async def export_conversation(
    request: ExportRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Export conversation to PDF/Markdown/JSON"""
    # Get all queries in session
    logs = db.query(QueryLog)\
        .filter(
            QueryLog.session_id == request.session_id,
            QueryLog.user_id == current_user.id
        )\
        .order_by(QueryLog.created_at)\
        .all()
    
    if not logs:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Export based on format
    if request.format == "json":
        return {
            "session_id": request.session_id,
            "user_id": current_user.id,
            "queries": [
                {
                    "query": log.query_text,
                    "answer": log.answer,
                    "timestamp": log.created_at.isoformat(),
                    "quality_score": log.quality_score
                }
                for log in logs
            ]
        }
    
    elif request.format == "pdf":
        # TODO: Implement PDF export
        raise HTTPException(status_code=501, detail="PDF export not yet implemented")
    
    else:  # markdown
        content = f"# Legal Query Session: {request.session_id}\n\n"
        content += f"**User:** {current_user.email}\n"
        content += f"**Date:** {logs[0].created_at.strftime('%Y-%m-%d %H:%M')}\n\n"
        content += "---\n\n"
        
        for i, log in enumerate(logs, 1):
            content += f"## Query {i}\n\n"
            content += f"**Q:** {log.query_text}\n\n"
            content += f"**A:** {log.answer}\n\n"
            content += f"*Quality Score: {log.quality_score:.2f}*\n\n"
            content += "---\n\n"
        
        return {"content": content, "format": "markdown"}


@router.post("/feedback")
async def submit_feedback(
    query_id: str = Query(..., description="Query ID to provide feedback for"),
    rating: int = Query(..., ge=1, le=5, description="Rating from 1-5"),
    feedback: Optional[str] = Query(None, description="Optional feedback text"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Submit feedback on a query response"""
    log = db.query(QueryLog).filter(
        QueryLog.query_id == query_id,
        QueryLog.user_id == current_user.id
    ).first()
    
    if not log:
        raise HTTPException(status_code=404, detail="Query not found")
    
    log.feedback_rating = rating
    log.feedback_text = feedback
    db.commit()
    
    return {"status": "success", "message": "Feedback recorded"}
