"""
Pydantic models for API requests and responses
Aligns with Patent Claim 18 requirements
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum


class DocumentContext(BaseModel):
    """Context document from retrieval"""
    model_config = ConfigDict(str_strip_whitespace=True)
    
    doc_id: str = Field(..., description="Document ID (e.g., 'sgca_2013_36_para_45')")
    content: str = Field(..., min_length=10, description="Paragraph text content")
    doc_type: str = Field(..., pattern="^(statute|case)$", description="Document type")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")


class ValidationRequest(BaseModel):
    """Request model for validation endpoint"""
    model_config = ConfigDict(str_strip_whitespace=True)
    
    query: str = Field(
        ..., 
        min_length=10, 
        max_length=1000,
        description="User's legal query"
    )
    answer: str = Field(
        ..., 
        min_length=50, 
        max_length=5000,
        description="Generated answer to validate"
    )
    context: List[DocumentContext] = Field(
        ..., 
        min_length=1,  # Changed from min_items
        max_length=20,  # Changed from max_items
        description="Retrieved context documents"
    )


class ValidationMetrics(BaseModel):
    """Validation metrics (from Week 5)"""
    synthesis_score: float = Field(..., ge=0.0, le=1.0)
    citation_precision: float = Field(..., ge=0.0, le=1.0)
    hallucination_rate: float = Field(..., ge=0.0, le=1.0)
    total_time_ms: float = Field(..., ge=0.0)
    stage_times: Dict[str, float] = Field(default_factory=dict)


class ValidationResponse(BaseModel):
    """Response model for validation (Patent Claim 15 compliance)"""
    correlation_id: str = Field(..., description="Unique tracking ID")
    decision: str = Field(..., pattern="^(PASS|REVIEW|REJECT)$")
    priority: str = Field(..., pattern="^(low|medium|high|critical|auto_reject)$")
    metrics: ValidationMetrics
    issues: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=datetime.now)


class BatchValidationRequest(BaseModel):
    """Batch validation request"""
    requests: List[ValidationRequest] = Field(..., max_length=100)  # Changed from max_items


class BatchValidationResponse(BaseModel):
    """Batch validation response"""
    results: List[ValidationResponse]
    total: int
    successful: int
    failed: int
    batch_id: str


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    timestamp: float
    version: str
    database: str
    components: Dict[str, str]


class ErrorResponse(BaseModel):
    """Error response"""
    error: str
    detail: str
    correlation_id: Optional[str] = None
