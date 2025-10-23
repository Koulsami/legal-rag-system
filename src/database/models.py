"""
SQLAlchemy models for Legal RAG system
Includes documents and interpretation_links tables
"""

from datetime import datetime
from typing import Optional, List
from sqlalchemy import (
    Column, String, Integer, Float, Boolean, Text, 
    ARRAY, TIMESTAMP, CheckConstraint, UniqueConstraint, Index
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import UUID
import uuid

Base = declarative_base()


class Document(Base):
    """Document table - stores statutes, cases, rules"""
    __tablename__ = 'documents'
    
    id = Column(String(255), primary_key=True)
    doc_type = Column(String(50), nullable=False)  # statute|case|rule
    title = Column(String(500), nullable=False)
    content = Column(Text, nullable=False)
    
    # Hierarchy support
    parent_id = Column(String(255), nullable=True)
    level = Column(Integer, default=0)
    
    # Citation metadata
    citation = Column(String(100), nullable=True)
    court = Column(String(50), nullable=True)
    year = Column(Integer, nullable=True)
    
    # Timestamps
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    updated_at = Column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_doc_type', 'doc_type'),
        Index('idx_citation', 'citation'),
        Index('idx_parent', 'parent_id'),
    )


class InterpretationLink(Base):
    """Interpretation links - pairs statutes with interpretive cases"""
    __tablename__ = 'interpretation_links'
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # References
    statute_id = Column(String(255), nullable=False)
    case_id = Column(String(255), nullable=False)
    
    # Denormalized statute details
    statute_name = Column(String(500), nullable=False)
    statute_section = Column(String(50), nullable=False)
    statute_text = Column(Text, nullable=True)
    
    # Denormalized case details
    case_name = Column(String(500), nullable=False)
    case_citation = Column(String(100), nullable=False)
    case_para_no = Column(Integer, nullable=False)
    case_text = Column(Text, nullable=True)
    court = Column(String(50), nullable=True)
    year = Column(Integer, nullable=True)
    
    # Interpretation metadata
    interpretation_type = Column(String(50), nullable=False)
    # NARROW | BROAD | CLARIFY | PURPOSIVE | LITERAL | APPLY
    
    authority = Column(String(50), nullable=False)
    # BINDING | PERSUASIVE | OBITER | DISSENT
    
    holding = Column(Text, nullable=False)
    
    # Fact pattern awareness (v2.0)
    fact_pattern_tags = Column(ARRAY(Text), nullable=True)
    case_facts_summary = Column(Text, nullable=True)
    applicability_score = Column(Float, default=0.8)
    
    # Extraction metadata
    extraction_method = Column(String(50), nullable=True)
    # RULE_BASED | LLM_ASSISTED | MANUAL
    
    confidence = Column(Float, nullable=True)
    
    # Verification
    verified = Column(Boolean, default=False)
    verified_by = Column(String(100), nullable=True)
    verified_at = Column(TIMESTAMP, nullable=True)
    
    # Retrieval weights
    boost_factor = Column(Float, default=1.5)
    
    # Timestamps
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    updated_at = Column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        UniqueConstraint('statute_id', 'case_id', name='unique_statute_case_pair'),
        CheckConstraint(
            "interpretation_type IN ('NARROW', 'BROAD', 'CLARIFY', 'PURPOSIVE', 'LITERAL', 'APPLY')",
            name='valid_interpretation_type'
        ),
        CheckConstraint(
            "authority IN ('BINDING', 'PERSUASIVE', 'OBITER', 'DISSENT')",
            name='valid_authority'
        ),
        CheckConstraint(
            "boost_factor >= 1.0 AND boost_factor <= 3.0",
            name='valid_boost_factor'
        ),
        CheckConstraint(
            "confidence >= 0.0 AND confidence <= 1.0",
            name='valid_confidence'
        ),
        Index('idx_statute_lookup', 'statute_id'),
        Index('idx_case_lookup', 'case_id'),
        Index('idx_verified', 'verified'),
        Index('idx_authority', 'authority'),
        Index('idx_applicability', 'applicability_score'),
    )


class IndexUnit(Base):
    """Index units - paragraph-level retrieval units"""
    __tablename__ = 'index_units'
    
    unit_id = Column(String(255), primary_key=True)
    doc_id = Column(String(255), nullable=False)
    doc_type = Column(String(50), nullable=False)
    
    # Content
    title = Column(String(500), nullable=True)
    text = Column(Text, nullable=False)
    
    # Metadata
    citation = Column(String(100), nullable=True)
    court = Column(String(50), nullable=True)
    year = Column(Integer, nullable=True)
    para_no = Column(Integer, nullable=True)
    
    # Embeddings (stored in FAISS, not here)
    # BM25 fields
    bm25_fields = Column(Text, nullable=True)  # JSON string
    
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_unit_doc', 'doc_id'),
        Index('idx_unit_type', 'doc_type'),
        Index('idx_unit_citation', 'citation'),
    )
