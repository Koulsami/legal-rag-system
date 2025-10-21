"""
Database models for Myk Raws Legal RAG system
SQLAlchemy ORM models for PostgreSQL
"""
from sqlalchemy import Column, Integer, String, Text, Float, Boolean, DateTime, ForeignKey, JSON, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import enum

from app.core.database import Base


# ===== ENUMS =====

class InterpretationType(str, enum.Enum):
    """Types of statutory interpretation"""
    NARROW = "NARROW"
    BROAD = "BROAD"
    CLARIFY = "CLARIFY"
    PURPOSIVE = "PURPOSIVE"
    LITERAL = "LITERAL"
    APPLY = "APPLY"


class AuthorityLevel(str, enum.Enum):
    """Authority level of case law"""
    BINDING = "BINDING"
    PERSUASIVE = "PERSUASIVE"
    OBITER = "OBITER"
    DISSENT = "DISSENT"


class DocumentType(str, enum.Enum):
    """Type of legal document"""
    STATUTE = "STATUTE"
    CASE = "CASE"
    REGULATION = "REGULATION"
    RULE = "RULE"


# ===== USER MANAGEMENT =====

class User(Base):
    """User account model"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    query_logs = relationship("QueryLog", back_populates="user")
    
    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}')>"


# ===== LEGAL DOCUMENTS =====

class LegalDocument(Base):
    """Legal document metadata (statutes and cases)"""
    __tablename__ = "legal_documents"

    id = Column(Integer, primary_key=True, index=True)
    doc_id = Column(String(255), unique=True, index=True, nullable=False)
    doc_type = Column(Enum(DocumentType), nullable=False, index=True)
    
    # Document metadata
    title = Column(Text, nullable=False)
    citation = Column(String(255), nullable=False, index=True)
    jurisdiction = Column(String(100), default="Singapore")
    court = Column(String(255))  # For cases
    year = Column(Integer, index=True)
    
    # Content
    full_text = Column(Text)
    summary = Column(Text)
    
    # Embeddings (stored as JSON array)
    embedding = Column(JSON)  # Array of floats
    
    # Metadata
    doc_metadata = Column(JSON)  # Renamed from metadata to avoid SQLAlchemy conflict  # Additional flexible metadata
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    interpretations_as_statute = relationship(
        "InterpretationLink",
        foreign_keys="InterpretationLink.statute_id",
        back_populates="statute"
    )
    interpretations_as_case = relationship(
        "InterpretationLink",
        foreign_keys="InterpretationLink.case_id",
        back_populates="case"
    )
    
    def __repr__(self):
        return f"<LegalDocument(doc_id='{self.doc_id}', type={self.doc_type})>"


# ===== INTERPRETATION LINKS (CORE FEATURE) =====

class InterpretationLink(Base):
    """
    Links between statutes and interpretive cases
    This is the PRIMARY innovation of the system
    """
    __tablename__ = "interpretation_links"

    id = Column(Integer, primary_key=True, index=True)
    
    # Foreign keys
    statute_id = Column(Integer, ForeignKey("legal_documents.id"), nullable=False, index=True)
    case_id = Column(Integer, ForeignKey("legal_documents.id"), nullable=False, index=True)
    
    # Interpretation metadata
    interpretation_type = Column(Enum(InterpretationType), nullable=False)
    authority_level = Column(Enum(AuthorityLevel), nullable=False)
    
    # Boost factor for retrieval (1.0 to 3.0)
    boost_factor = Column(Float, default=2.0)
    
    # Optional description
    description = Column(Text)
    
    # Verification status
    is_verified = Column(Boolean, default=False)
    verified_by = Column(String(255))
    verification_date = Column(DateTime(timezone=True))
    
    # Extraction metadata
    extraction_method = Column(String(100))  # "manual", "llm", "rule_based"
    confidence_score = Column(Float)  # 0.0 to 1.0
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    statute = relationship(
        "LegalDocument",
        foreign_keys=[statute_id],
        back_populates="interpretations_as_statute"
    )
    case = relationship(
        "LegalDocument",
        foreign_keys=[case_id],
        back_populates="interpretations_as_case"
    )
    
    def __repr__(self):
        return (
            f"<InterpretationLink("
            f"statute_id={self.statute_id}, "
            f"case_id={self.case_id}, "
            f"type={self.interpretation_type})>"
        )


# ===== DOCUMENT CHUNKS =====

class DocumentChunk(Base):
    """
    Chunked text from legal documents for retrieval
    Each chunk is indexed separately in FAISS
    """
    __tablename__ = "document_chunks"

    id = Column(Integer, primary_key=True, index=True)
    
    # Parent document
    document_id = Column(Integer, ForeignKey("legal_documents.id"), nullable=False, index=True)
    
    # Chunk metadata
    chunk_index = Column(Integer, nullable=False)
    chunk_text = Column(Text, nullable=False)
    chunk_size = Column(Integer)  # Number of characters
    
    # Section information
    section_number = Column(String(50))
    section_title = Column(String(500))
    
    # Embeddings
    embedding = Column(JSON)  # Array of floats for semantic search
    
    # BM25 metadata
    bm25_terms = Column(JSON)  # Preprocessed terms for BM25
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationship
    document = relationship("LegalDocument")
    
    def __repr__(self):
        return f"<DocumentChunk(id={self.id}, document_id={self.document_id})>"


# ===== QUERY LOGS =====

class QueryLog(Base):
    """
    Log of user queries for analytics and improvement
    """
    __tablename__ = "query_logs"

    id = Column(Integer, primary_key=True, index=True)
    query_id = Column(String(255), unique=True, index=True, nullable=False)
    session_id = Column(String(255), index=True)
    
    # User
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Query details
    query_text = Column(Text, nullable=False)
    answer = Column(Text)
    
    # Retrieved documents
    context_documents = Column(Integer)  # Count
    interpretation_links_used = Column(Integer, default=0)
    
    # Performance metrics
    processing_time = Column(Float)  # Seconds
    retrieval_time = Column(Float)
    generation_time = Column(Float)
    
    # Quality metrics
    quality_score = Column(Float)
    citation_precision = Column(Float)
    hallucination_score = Column(Float)
    interpretation_coverage = Column(Float)
    
    # User feedback
    feedback_rating = Column(Integer)  # 1-5
    feedback_text = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationship
    user = relationship("User", back_populates="query_logs")
    
    def __repr__(self):
        return f"<QueryLog(query_id='{self.query_id}', user_id={self.user_id})>"


# ===== SYSTEM METRICS =====

class SystemMetrics(Base):
    """
    System performance and usage metrics
    """
    __tablename__ = "system_metrics"

    id = Column(Integer, primary_key=True, index=True)
    
    # Metrics
    metric_name = Column(String(255), nullable=False, index=True)
    metric_value = Column(Float, nullable=False)
    metric_unit = Column(String(50))
    
    # Context
    context = Column(JSON)  # Additional context data
    
    # Timestamp
    recorded_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    def __repr__(self):
        return f"<SystemMetrics(name='{self.metric_name}', value={self.metric_value})>"


# ===== VALIDATION RESULTS =====

class ValidationResult(Base):
    """
    Results of response validation checks
    """
    __tablename__ = "validation_results"

    id = Column(Integer, primary_key=True, index=True)
    
    # Associated query
    query_id = Column(String(255), ForeignKey("query_logs.query_id"), index=True)
    
    # Validation checks
    citation_check_passed = Column(Boolean)
    hallucination_check_passed = Column(Boolean)
    interpretation_check_passed = Column(Boolean)
    synthesis_quality_passed = Column(Boolean)
    
    # Detailed results
    validation_details = Column(JSON)
    
    # Warnings and errors
    warnings = Column(JSON)
    errors = Column(JSON)
    
    # Timestamp
    validated_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<ValidationResult(query_id='{self.query_id}')>"


# ===== HELPER FUNCTIONS =====

def get_boost_factor(authority_level: AuthorityLevel) -> float:
    """Get default boost factor for authority level"""
    boost_map = {
        AuthorityLevel.BINDING: 3.0,
        AuthorityLevel.PERSUASIVE: 2.0,
        AuthorityLevel.OBITER: 1.5,
        AuthorityLevel.DISSENT: 1.2,
    }
    return boost_map.get(authority_level, 2.0)


def create_interpretation_link(
    statute_id: int,
    case_id: int,
    interpretation_type: InterpretationType,
    authority_level: AuthorityLevel,
    **kwargs
) -> InterpretationLink:
    """Factory function to create interpretation link with defaults"""
    return InterpretationLink(
        statute_id=statute_id,
        case_id=case_id,
        interpretation_type=interpretation_type,
        authority_level=authority_level,
        boost_factor=get_boost_factor(authority_level),
        **kwargs
    )
