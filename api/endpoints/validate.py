"""
Validation endpoints for FastAPI
Provides single and batch validation with background processing
"""
from datetime import datetime
from typing import List, Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException, Header
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import Session

from api.utils.database import get_db
from validation.integrated_validation_pipeline import validate_answer
from validation.correlation_id import correlation_context
from validation.logging_config import get_logger

router = APIRouter()
logger = get_logger(__name__)

# ============================================================================
# Pydantic Models
# ============================================================================

class ContextDocument(BaseModel):
    """Retrieved context document"""
    doc_id: str = Field(..., description="Document ID")
    content: str = Field(..., description="Document content")
    doc_type: str = Field(..., description="Document type (statute/case)")
    score: Optional[float] = Field(None, description="Retrieval score")


class ValidationRequest(BaseModel):
    """Single validation request"""
    query: str = Field(..., min_length=10, description="User query")
    answer: str = Field(..., min_length=50, description="Generated answer")
    context: List[ContextDocument] = Field(..., min_length=1, max_length=20)
    
    @field_validator('context')
    @classmethod
    def validate_context(cls, v):
        if not v:
            raise ValueError("Context cannot be empty")
        if len(v) > 20:
            raise ValueError("Context cannot exceed 20 documents")
        return v


class ValidationMetrics(BaseModel):
    """Validation metrics"""
    synthesis_score: float
    citation_score: float
    hallucination_rate: float
    total_time_ms: float


class ValidationResponse(BaseModel):
    """Validation response"""
    correlation_id: str
    decision: str  # "pass", "review", "reject"
    priority: Optional[str]  # "low", "medium", "high", "critical"
    metrics: ValidationMetrics
    issues: List[str]
    warnings: List[str]
    timestamp: datetime


class BatchValidationRequest(BaseModel):
    """Batch validation request"""
    requests: List[ValidationRequest] = Field(..., min_length=1, max_length=50)
    
    @field_validator('requests')
    @classmethod
    def validate_batch_size(cls, v):
        if len(v) > 50:
            raise ValueError("Batch size cannot exceed 50")
        return v


class BatchValidationResponse(BaseModel):
    """Batch validation response"""
    batch_id: str
    total: int
    results: List[ValidationResponse]
    failed: List[dict]
    timestamp: datetime


# ============================================================================
# Authentication
# ============================================================================

VALID_API_KEYS = {
    "dev_key_12345": "development",
    "prod_key_67890": "production",
}


def verify_api_key(x_api_key: str = Header(...)) -> str:
    """
    Verify API key from header
    
    Args:
        x_api_key: API key from X-API-Key header
        
    Returns:
        str: API key type (development/production)
        
    Raises:
        HTTPException: If API key is invalid
    """
    if x_api_key not in VALID_API_KEYS:
        logger.warning(f"Invalid API key attempt: {x_api_key[:10]}...")
        raise HTTPException(
            status_code=401,
            detail="Invalid API key"
        )
    
    api_type = VALID_API_KEYS[x_api_key]
    logger.info(f"API key validated: {api_type}")
    return api_type


# ============================================================================
# Background Tasks
# ============================================================================

def store_validation_result(
    correlation_id: str,
    request: ValidationRequest,
    result,
    db: Session
):
    """
    Store validation result in database (background task)
    
    Args:
        correlation_id: Unique request ID
        request: Original request
        result: Validation result
        db: Database session
    """
    try:
        # Store in validation_results table
        # This would be implemented with SQLAlchemy models
        logger.info(
            f"Stored validation result",
            extra={
                'correlation_id': correlation_id,
                'data': {
                    'decision': result.decision.value,
                    'synthesis_score': result.metrics.synthesis_score
                }
            }
        )
    except Exception as e:
        logger.error(
            f"Failed to store validation result: {e}",
            extra={'correlation_id': correlation_id}
        )


# ============================================================================
# Endpoints
# ============================================================================

@router.post("/validate", response_model=ValidationResponse)
async def validate_endpoint(
    request: ValidationRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    """
    Validate a single answer
    
    **Authentication:** Required (X-API-Key header)
    
    **Request:**
    - query: User query (min 10 chars)
    - answer: Generated answer (min 50 chars)
    - context: Retrieved documents (1-20 docs)
    
    **Response:**
    - correlation_id: Unique request ID
    - decision: pass/review/reject
    - priority: low/medium/high/critical (if review)
    - metrics: Validation metrics
    - issues: List of detected issues
    - warnings: List of warnings
    
    **Example:**
    ```bash
    curl -X POST http://localhost:8000/api/v1/validate \\
      -H "X-API-Key: dev_key_12345" \\
      -H "Content-Type: application/json" \\
      -d '{
        "query": "What is the test for inventive step?",
        "answer": "The test is...",
        "context": [{"doc_id": "statute_1", "content": "...", "doc_type": "statute"}]
      }'
    ```
    """
    with correlation_context() as corr_id:
        logger.info(
            "API validation request",
            extra={
                'correlation_id': corr_id,
                'data': {
                    'api_key_type': api_key,
                    'query_length': len(request.query),
                    'answer_length': len(request.answer),
                    'context_count': len(request.context)
                }
            }
        )
        
        try:
            # Convert context to dict format
            context = [
                {
                    'doc_id': doc.doc_id,
                    'content': doc.content,
                    'doc_type': doc.doc_type
                }
                for doc in request.context
            ]
            
            # Run validation
            result = validate_answer(
                request.answer,
                request.query,
                context,
                db
            )
            
            # Convert to response
            response = ValidationResponse(
                correlation_id=corr_id,
                decision=result.decision.value,
                priority=result.priority,
                metrics=ValidationMetrics(
                    synthesis_score=result.metrics.synthesis_score,
                    citation_score=result.metrics.citation_score,
                    hallucination_rate=result.metrics.hallucination_rate,
                    total_time_ms=result.metrics.total_time_ms
                ),
                issues=result.issues,
                warnings=result.warnings,
                timestamp=datetime.now()
            )
            
            # Store result in background
            background_tasks.add_task(
                store_validation_result,
                corr_id,
                request,
                result,
                db
            )
            
            logger.info(
                "Validation completed",
                extra={
                    'correlation_id': corr_id,
                    'data': {
                        'decision': result.decision.value,
                        'synthesis_score': result.metrics.synthesis_score,
                        'hallucination_rate': result.metrics.hallucination_rate
                    }
                }
            )
            
            return response
            
        except Exception as e:
            logger.error(
                f"Validation failed: {e}",
                extra={'correlation_id': corr_id},
                exc_info=True
            )
            raise HTTPException(
                status_code=500,
                detail=f"Validation failed: {str(e)}"
            )


@router.post("/validate/batch", response_model=BatchValidationResponse)
async def batch_validate_endpoint(
    request: BatchValidationRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    """
    Validate multiple answers in batch
    
    **Authentication:** Required (X-API-Key header)
    
    **Limits:** Max 50 requests per batch
    
    **Request:**
    - requests: List of validation requests
    
    **Response:**
    - batch_id: Unique batch ID
    - total: Total requests
    - results: Successful validations
    - failed: Failed validations with errors
    
    **Example:**
    ```bash
    curl -X POST http://localhost:8000/api/v1/validate/batch \\
      -H "X-API-Key: dev_key_12345" \\
      -H "Content-Type: application/json" \\
      -d '{
        "requests": [
          {"query": "...", "answer": "...", "context": [...]},
          {"query": "...", "answer": "...", "context": [...]}
        ]
      }'
    ```
    """
    batch_id = str(uuid4())
    
    logger.info(
        "Batch validation request",
        extra={
            'correlation_id': batch_id,
            'data': {
                'api_key_type': api_key,
                'batch_size': len(request.requests)
            }
        }
    )
    
    results = []
    failed = []
    
    for idx, val_req in enumerate(request.requests):
        try:
            with correlation_context() as corr_id:
                # Convert context
                context = [
                    {
                        'doc_id': doc.doc_id,
                        'content': doc.content,
                        'doc_type': doc.doc_type
                    }
                    for doc in val_req.context
                ]
                
                # Run validation
                result = validate_answer(
                    val_req.answer,
                    val_req.query,
                    context,
                    db
                )
                
                # Add to results
                results.append(ValidationResponse(
                    correlation_id=corr_id,
                    decision=result.decision.value,
                    priority=result.priority,
                    metrics=ValidationMetrics(
                        synthesis_score=result.metrics.synthesis_score,
                        citation_score=result.metrics.citation_score,
                        hallucination_rate=result.metrics.hallucination_rate,
                        total_time_ms=result.metrics.total_time_ms
                    ),
                    issues=result.issues,
                    warnings=result.warnings,
                    timestamp=datetime.now()
                ))
                
                # Store in background
                background_tasks.add_task(
                    store_validation_result,
                    corr_id,
                    val_req,
                    result,
                    db
                )
                
        except Exception as e:
            logger.error(
                f"Batch item {idx} failed: {e}",
                extra={'correlation_id': batch_id}
            )
            failed.append({
                'index': idx,
                'error': str(e),
                'query': val_req.query[:100]
            })
    
    logger.info(
        "Batch validation completed",
        extra={
            'correlation_id': batch_id,
            'data': {
                'total': len(request.requests),
                'succeeded': len(results),
                'failed': len(failed)
            }
        }
    )
    
    return BatchValidationResponse(
        batch_id=batch_id,
        total=len(request.requests),
        results=results,
        failed=failed,
        timestamp=datetime.now()
    )
