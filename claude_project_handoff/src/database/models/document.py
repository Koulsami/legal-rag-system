"""
Document model with hierarchical tree structure support.
"""

from typing import List, Optional, Dict, Any
from datetime import date, datetime
from enum import Enum

from sqlalchemy import (
    Column, String, Text, Integer, Date, DateTime, 
    ForeignKey, Index, CheckConstraint, ARRAY, Float
)
from sqlalchemy.orm import relationship, Session
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.hybrid import hybrid_property

from .base import Base, TimestampMixin


class DocType(str, Enum):
    """Document type enumeration."""
    STATUTE = "statute"
    CASE = "case"
    RULE = "rule"
    COMMENTARY = "commentary"


class Outcome(str, Enum):
    """Case outcome enumeration."""
    GRANTED = "granted"
    DISMISSED = "dismissed"
    SETTLED = "settled"
    PARTIALLY_GRANTED = "partially_granted"
    WITHDRAWN = "withdrawn"


class Document(Base, TimestampMixin):
    """Document model supporting both statutes and cases with tree structure."""
    
    __tablename__ = "documents"
    
    # Primary Key & Core Fields
    id = Column(String(255), primary_key=True, comment="Document ID")
    doc_type = Column(String(50), nullable=False, index=True, comment="Document type")
    
    # Tree Structure Fields
    parent_id = Column(String(255), ForeignKey("documents.id", ondelete="CASCADE"), 
                      nullable=True, index=True, comment="Parent document ID")
    level = Column(Integer, nullable=False, default=0, 
                  comment="Hierarchy level: 0=root, 1=section, 2=subsection, 3=paragraph")
    
    # Document Metadata
    title = Column(Text, nullable=True, comment="Document title")
    citation = Column(String(200), nullable=True, index=True, comment="Legal citation")
    court = Column(String(50), nullable=True, index=True, comment="Court abbreviation")
    year = Column(Integer, nullable=True, index=True, comment="Year of decision")
    date = Column(Date, nullable=True, comment="Date of decision")
    jurisdiction = Column(String(50), nullable=False, default="Singapore", comment="Jurisdiction")
    url = Column(Text, nullable=True, comment="Source URL")
    hash = Column(String(64), unique=True, nullable=True, comment="SHA-256 hash")
    
    # Statutory Fields
    section_number = Column(String(50), nullable=True, comment="Section number")
    section_title = Column(Text, nullable=True, comment="Section heading")
    act_name = Column(String(500), nullable=True, comment="Act name")          # ADD THIS
    subsection = Column(String(50), nullable=True, comment="Subsection marker") # ADD THIS

    # Case-specific fields
    parties = Column(String(500), nullable=True, comment="Party names")         # ADD THIS
    
    # Case Diagnostic Fields
    facts_summary = Column(Text, nullable=True, comment="Brief case facts")
    cause_of_action = Column(String(200), nullable=True, index=True, comment="Primary legal issue")
    outcome = Column(String(50), nullable=True, index=True, comment="Case outcome")
    remedy_awarded = Column(Text, nullable=True, comment="Relief granted")
    defense_raised = Column(Text, nullable=True, comment="Defense arguments")
    
    # Case Paragraph Fields
    para_no = Column(Integer, nullable=True, comment="Paragraph number")
    
    # Full Text
    full_text = Column(Text, nullable=False, comment="Complete document text")
    
    # Flexible Metadata
    doc_metadata = Column(JSONB, nullable=True, default={}, comment="Additional metadata")
    
    # Relationships
    children = relationship("Document", backref="parent", remote_side=[id], 
                          cascade="all, delete")
    
    interpretations_as_statute = relationship(
        "InterpretationLink",
        foreign_keys="InterpretationLink.statute_id",
        back_populates="statute_document",
        cascade="all, delete-orphan"
    )
    
    interpretations_as_case = relationship(
        "InterpretationLink",
        foreign_keys="InterpretationLink.case_id",
        back_populates="case_document",
        cascade="all, delete-orphan"
    )
    
    # Table Constraints
    __table_args__ = (
        CheckConstraint("level >= 0 AND level <= 3", name="ck_valid_level"),
       # Index("ix_full_text_search", "full_text", postgresql_using="gin"),
       # Index("ix_facts_summary_trgm", "facts_summary", postgresql_using="gin",
        #      postgresql_ops={"facts_summary": "gin_trgm_ops"}),
        Index("ix_case_lookup", "doc_type", "cause_of_action", "outcome"),
        Index("ix_tree_lookup", "parent_id", "level"),
    )
    
    # Hybrid Properties
    @hybrid_property
    def is_statute(self) -> bool:
        """Check if document is a statute."""
        return self.doc_type == DocType.STATUTE.value
    
    @hybrid_property
    def is_case(self) -> bool:
        """Check if document is a case."""
        return self.doc_type == DocType.CASE.value
    
    @hybrid_property
    def is_root(self) -> bool:
        """Check if document is a root node."""
        return self.parent_id is None
    
    @hybrid_property
    def is_leaf(self) -> bool:
        """Check if document is a leaf node."""
        return len(self.children) == 0
    
    # Helper Methods
    def get_ancestors(self, session: Session) -> List["Document"]:
        """Get all ancestor documents."""
        ancestors = []
        current = self
        
        while current.parent_id:
            parent = session.query(Document).filter_by(id=current.parent_id).first()
            if parent:
                ancestors.append(parent)
                current = parent
            else:
                break
        
        return ancestors
    
    def get_descendants(self, session: Session, max_depth: Optional[int] = None) -> List["Document"]:
        """Get all descendant documents."""
        descendants = []
        
        def _traverse(node: "Document", depth: int = 0):
            if max_depth is not None and depth >= max_depth:
                return
            
            for child in node.children:
                descendants.append(child)
                _traverse(child, depth + 1)
        
        _traverse(self)
        return descendants
    
    def get_siblings(self, session: Session) -> List["Document"]:
        """Get sibling documents."""
        if not self.parent_id:
            return []
        
        return session.query(Document).filter(
            Document.parent_id == self.parent_id,
            Document.id != self.id
        ).order_by(Document.id).all()
    
    def build_complete_provision(self, session: Session) -> str:
        """Build complete provision text including all subsections."""
        if self.level >= 2:
            parent = session.query(Document).filter_by(id=self.parent_id).first()
            if parent:
                return parent.build_complete_provision(session)
        
        result = []
        
        if self.section_title:
            result.append(self.section_title)
            result.append("")
        
        result.append(self.full_text)
        result.append("")
        
        for child in sorted(self.children, key=lambda c: c.id):
            result.append(child.full_text)
        
        return "\n".join(result)
    
    def to_dict(self, include_relationships: bool = False) -> Dict[str, Any]:
        """Convert document to dictionary."""
        data = {
            "id": self.id,
            "doc_type": self.doc_type,
            "parent_id": self.parent_id,
            "level": self.level,
            "title": self.title,
            "citation": self.citation,
            "court": self.court,
            "year": self.year,
            "date": self.date.isoformat() if self.date else None,
            "jurisdiction": self.jurisdiction,
            "section_number": self.section_number,
            "section_title": self.section_title,
            "facts_summary": self.facts_summary,
            "cause_of_action": self.cause_of_action,
            "outcome": self.outcome,
            "remedy_awarded": self.remedy_awarded,
            "para_no": self.para_no,
            "full_text": self.full_text[:200] + "..." if len(self.full_text) > 200 else self.full_text,
            "metadata": self.doc_metadata,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
        
        if include_relationships:
            data["children_ids"] = [child.id for child in self.children]
            data["num_children"] = len(self.children)
        
        return data
    
    def __repr__(self) -> str:
        """String representation."""
        return f"Document(id='{self.id}', type='{self.doc_type}', level={self.level})"
