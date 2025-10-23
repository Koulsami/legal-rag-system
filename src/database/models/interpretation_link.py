"""
Interpretation link model with fact-pattern awareness.
This is the PRIMARY INNOVATION of the Legal Diagnostic RAG system.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum
from uuid import uuid4

from sqlalchemy import (
    Column, String, Text, Integer, Float, Boolean,
    ForeignKey, Index, CheckConstraint, ARRAY, DateTime
)
from sqlalchemy.orm import relationship, Session
from sqlalchemy.dialects.postgresql import UUID, ARRAY as PG_ARRAY
from sqlalchemy.ext.hybrid import hybrid_property

from .base import Base, TimestampMixin


class InterpretationType(str, Enum):
    """How the case interprets the statute."""
    NARROW = "NARROW"
    BROAD = "BROAD"
    CLARIFY = "CLARIFY"
    PURPOSIVE = "PURPOSIVE"
    LITERAL = "LITERAL"
    APPLY = "APPLY"


class Authority(str, Enum):
    """Legal authority level of the interpretation."""
    BINDING = "BINDING"
    PERSUASIVE = "PERSUASIVE"
    OBITER = "OBITER"
    DISSENT = "DISSENT"


class InterpretationLink(Base, TimestampMixin):
    """Links statute sections to interpretive case paragraphs."""
    
    __tablename__ = "interpretation_links"
    
    # Primary Key & References
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4, comment="Primary key")
    statute_id = Column(String(255), ForeignKey("documents.id", ondelete="CASCADE"),
                       nullable=False, index=True, comment="Statute document ID")
    case_id = Column(String(255), ForeignKey("documents.id", ondelete="CASCADE"),
                    nullable=False, index=True, comment="Case document ID")
    
    # Denormalized Statute Details
    statute_name = Column(String(500), nullable=False, comment="Full statute name")
    statute_section = Column(String(50), nullable=False, index=True, comment="Section number")
    statute_text = Column(Text, nullable=True, comment="Statute text snippet")
    
    # Denormalized Case Details
    case_name = Column(String(500), nullable=False, comment="Case name")
    case_citation = Column(String(100), nullable=False, index=True, comment="Case citation")
    case_para_no = Column(Integer, nullable=False, comment="Paragraph number")
    case_text = Column(Text, nullable=True, comment="Case paragraph text")
    court = Column(String(50), nullable=True, index=True, comment="Court abbreviation")
    year = Column(Integer, nullable=True, index=True, comment="Year of decision")
    
    # Interpretation Metadata
    interpretation_type = Column(String(50), nullable=False, index=True,
                                comment="How case interprets statute")
    authority = Column(String(50), nullable=False, index=True, comment="Legal authority level")
    holding = Column(Text, nullable=False, comment="Brief description of interpretation")
    
    # FACT PATTERN AWARENESS (PRIMARY INNOVATION)
    fact_pattern_tags = Column(PG_ARRAY(Text), nullable=True,
                              comment="Tags describing fact pattern")
    case_facts_summary = Column(Text, nullable=True, comment="Brief case facts")
    applicability_score = Column(Float, nullable=True,
                                comment="How broadly applicable (0-1)")
    cause_of_action = Column(String(100), nullable=True, index=True,
                            comment="Primary legal issue")
    sub_issues = Column(PG_ARRAY(Text), nullable=True, comment="Specific issues addressed")
    
    # Retrieval Configuration
    boost_factor = Column(Float, nullable=False, default=2.0,
                         comment="Retrieval boost multiplier")
    verified = Column(Boolean, nullable=False, default=False, comment="Manually verified")
    verified_by = Column(String(100), nullable=True, comment="User who verified")
    verified_at = Column(DateTime, nullable=True, comment="When verified")
    
    # Extraction Metadata
    extraction_method = Column(String(50), nullable=True,
                              comment="How link was extracted")
    extraction_confidence = Column(Float, nullable=True, comment="Extraction confidence")
    notes = Column(Text, nullable=True, comment="Additional notes")
    
    # Relationships
    statute_document = relationship(
        "Document",
        foreign_keys=[statute_id],
        back_populates="interpretations_as_statute"
    )
    
    case_document = relationship(
        "Document",
        foreign_keys=[case_id],
        back_populates="interpretations_as_case"
    )
    
    # Table Constraints
    __table_args__ = (
        CheckConstraint("boost_factor >= 1.0 AND boost_factor <= 5.0",
                       name="ck_valid_boost_factor"),
        CheckConstraint("applicability_score IS NULL OR (applicability_score >= 0 AND applicability_score <= 1)",
                       name="ck_valid_applicability_score"),
        CheckConstraint("extraction_confidence IS NULL OR (extraction_confidence >= 0 AND extraction_confidence <= 1)",
                       name="ck_valid_confidence"),
        Index("ix_unique_interpretation", "statute_id", "case_id", unique=True),
      #  Index("ix_fact_pattern_lookup", "cause_of_action", "fact_pattern_tags",
       #       postgresql_using="gin"),
       # Index("ix_case_facts_trgm", "case_facts_summary", postgresql_using="gin",
        #      postgresql_ops={"case_facts_summary": "gin_trgm_ops"}),
        Index("ix_retrieval_lookup", "statute_id", "boost_factor", "applicability_score"),
    )
    
    # Hybrid Properties
    @hybrid_property
    def is_binding(self) -> bool:
        """Check if interpretation has binding authority."""
        return self.authority == Authority.BINDING.value
    
    @hybrid_property
    def is_verified(self) -> bool:
        """Check if link has been manually verified."""
        return self.verified
    
    @hybrid_property
    def is_high_confidence(self) -> bool:
        """Check if extraction confidence is high."""
        return self.extraction_confidence is not None and self.extraction_confidence > 0.8
    
    @hybrid_property
    def effective_boost(self) -> float:
        """Calculate effective boost considering applicability score."""
        if self.applicability_score:
            return self.boost_factor * self.applicability_score
        return self.boost_factor
    
    # Helper Methods
    def matches_fact_pattern(self, user_tags: List[str]) -> bool:
        """Check if interpretation matches user's fact pattern."""
        if not self.fact_pattern_tags or not user_tags:
            return False
        return bool(set(self.fact_pattern_tags) & set(user_tags))
    
    def fact_overlap_score(self, user_tags: List[str]) -> float:
        """Calculate Jaccard similarity of fact pattern tags."""
        if not self.fact_pattern_tags or not user_tags:
            return 0.0
        
        link_set = set(self.fact_pattern_tags)
        user_set = set(user_tags)
        
        intersection = len(link_set & user_set)
        union = len(link_set | user_set)
        
        return intersection / union if union > 0 else 0.0
    
    def verify(self, user: str) -> None:
        """Mark interpretation link as verified."""
        self.verified = True
        self.verified_by = user
        self.verified_at = datetime.utcnow()
    
    def to_dict(self, include_relationships: bool = False) -> Dict[str, Any]:
        """Convert interpretation link to dictionary."""
        data = {
            "id": str(self.id),
            "statute_id": self.statute_id,
            "case_id": self.case_id,
            "statute_name": self.statute_name,
            "statute_section": self.statute_section,
            "case_name": self.case_name,
            "case_citation": self.case_citation,
            "case_para_no": self.case_para_no,
            "court": self.court,
            "year": self.year,
            "interpretation_type": self.interpretation_type,
            "authority": self.authority,
            "holding": self.holding,
            "fact_pattern_tags": self.fact_pattern_tags,
            "case_facts_summary": self.case_facts_summary,
            "applicability_score": self.applicability_score,
            "cause_of_action": self.cause_of_action,
            "sub_issues": self.sub_issues,
            "boost_factor": self.boost_factor,
            "effective_boost": self.effective_boost,
            "verified": self.verified,
            "verified_by": self.verified_by,
            "verified_at": self.verified_at.isoformat() if self.verified_at else None,
            "extraction_method": self.extraction_method,
            "extraction_confidence": self.extraction_confidence,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
        
        if include_relationships:
            data["statute_text"] = self.statute_text
            data["case_text"] = self.case_text
        
        return data
    
    def __repr__(self) -> str:
        """String representation."""
        return (
            f"InterpretationLink("
            f"statute='{self.statute_section}', "
            f"case='{self.case_citation} ¶{self.case_para_no}', "
            f"type='{self.interpretation_type}'"
            f")"
        )


class InterpretationLinkBuilder:
    """Builder pattern for creating interpretation links."""
    
    def __init__(self):
        self._link = InterpretationLink()
    
    def with_statute(self, statute_id: str, statute_name: str, statute_section: str,
                    statute_text: Optional[str] = None) -> "InterpretationLinkBuilder":
        """Set statute information."""
        self._link.statute_id = statute_id
        self._link.statute_name = statute_name
        self._link.statute_section = statute_section
        self._link.statute_text = statute_text
        return self
    
    def with_case(self, case_id: str, case_name: str, case_citation: str,
                 case_para_no: int, court: Optional[str] = None,
                 year: Optional[int] = None, case_text: Optional[str] = None) -> "InterpretationLinkBuilder":
        """Set case information."""
        self._link.case_id = case_id
        self._link.case_name = case_name
        self._link.case_citation = case_citation
        self._link.case_para_no = case_para_no
        self._link.court = court
        self._link.year = year
        self._link.case_text = case_text
        return self
    
    def with_interpretation(self, interpretation_type: str, authority: str,
                          holding: str) -> "InterpretationLinkBuilder":
        """Set interpretation metadata."""
        self._link.interpretation_type = interpretation_type
        self._link.authority = authority
        self._link.holding = holding
        return self
    
    def with_fact_pattern(self, tags: List[str], case_facts_summary: str,
                         applicability_score: float = 0.7,
                         cause_of_action: Optional[str] = None,
                         sub_issues: Optional[List[str]] = None) -> "InterpretationLinkBuilder":
        """Set fact-pattern information."""
        self._link.fact_pattern_tags = tags
        self._link.case_facts_summary = case_facts_summary
        self._link.applicability_score = applicability_score
        self._link.cause_of_action = cause_of_action
        self._link.sub_issues = sub_issues
        return self
    
    def with_boost(self, boost_factor: float) -> "InterpretationLinkBuilder":
        """Set boost factor."""
        self._link.boost_factor = boost_factor
        return self
    
    def with_extraction_metadata(self, method: str, confidence: float,
                                notes: Optional[str] = None) -> "InterpretationLinkBuilder":
        """Set extraction metadata."""
        self._link.extraction_method = method
        self._link.extraction_confidence = confidence
        self._link.notes = notes
        return self
    
    def build(self) -> InterpretationLink:
        """Build and return the interpretation link."""
        if not self._link.statute_id:
            raise ValueError("statute_id is required")
        if not self._link.case_id:
            raise ValueError("case_id is required")
        if not self._link.interpretation_type:
            raise ValueError("interpretation_type is required")
        if not self._link.authority:
            raise ValueError("authority is required")
        if not self._link.holding:
            raise ValueError("holding is required")
        
        return self._link
