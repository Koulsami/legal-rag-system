"""
Data models for document ingestion pipeline.

This module defines Pydantic models for:
- Raw source documents (before parsing)
- Parsed documents (after extraction)
- Ingestion results (statistics and errors)
"""

from typing import Optional, List, Dict, Any, Literal
from datetime import datetime
from pydantic import BaseModel, Field, validator
import hashlib


# ============================================================================
# Core Data Models
# ============================================================================

class SourceDocument(BaseModel):
    """Raw document from source (before parsing)"""
    
    filepath: str = Field(..., description="Path to source file")
    source_type: Literal["statute", "case", "rule", "commentary"] = Field(
        ..., description="Document type"
    )
    format: Literal["pdf", "html", "txt", "json"] = Field(
        ..., description="File format"
    )
    raw_content: Optional[str] = Field(None, description="Raw text content")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Source metadata")
    
    @validator('filepath')
    def validate_filepath(cls, v):
        """Ensure filepath is non-empty"""
        if not v or not v.strip():
            raise ValueError("Filepath cannot be empty")
        return v.strip()


class ParsedDocument(BaseModel):
    """Parsed document ready for database insertion"""
    
    # Required fields
    id: str = Field(..., description="Unique document ID")
    doc_type: Literal["statute", "case", "rule", "commentary"]
    title: str = Field(..., description="Document title")
    full_text: str = Field(..., description="Full document text")
    
    # Hierarchy
    parent_id: Optional[str] = Field(None, description="Parent document ID")
    level: int = Field(0, ge=0, le=5, description="Hierarchy level (0=root)")
    
    # Metadata
    citation: Optional[str] = None
    jurisdiction: str = Field(default="SG", description="Jurisdiction code")
    year: Optional[int] = Field(None, ge=1800, le=2100)
    
    # Statute-specific
    act_name: Optional[str] = None
    section_number: Optional[str] = None
    subsection: Optional[str] = None
    
    # Case-specific
    court: Optional[str] = None
    para_no: Optional[int] = Field(None, ge=1)
    parties: Optional[str] = None
    
    # Diagnostic fields (CRITICAL for fact-pattern matching)
    facts_summary: Optional[str] = Field(
        None, 
        description="Brief case facts for similarity matching"
    )
    cause_of_action: Optional[str] = Field(
        None,
        description="Legal cause (e.g., 'Misrepresentation', 'Breach of Contract')"
    )
    outcome: Optional[str] = Field(
        None,
        description="Case outcome: granted, dismissed, settled, etc."
    )
    remedy_awarded: Optional[str] = None
    
    # Source tracking
    source_url: Optional[str] = None
    hash: str = Field(..., description="SHA-256 content hash for deduplication")
    
    class Config:
        """Pydantic configuration"""
        json_schema_extra = {
            "example": {
                "id": "sg_statute_misrep_act_s2",
                "doc_type": "statute",
                "title": "Section 2",
                "full_text": "Where a person has entered into a contract...",
                "parent_id": "sg_statute_misrep_act",
                "level": 1,
                "citation": "Misrepresentation Act (Cap 390)",
                "jurisdiction": "SG",
                "year": 1967,
                "act_name": "Misrepresentation Act",
                "section_number": "2",
                "hash": "abc123..."
            }
        }
    
    @validator('hash', pre=True, always=True)
    def generate_hash(cls, v, values):
        """Auto-generate hash from full_text if not provided"""
        if not v and 'full_text' in values:
            return hashlib.sha256(
                values['full_text'].encode('utf-8')
            ).hexdigest()
        return v
    
    @validator('level')
    def validate_level_with_parent(cls, v, values):
        """Ensure level > 0 requires parent_id"""
        if v > 0 and not values.get('parent_id'):
            raise ValueError("Documents with level > 0 must have parent_id")
        return v


class Section(BaseModel):
    """Represents a statutory section or case paragraph"""
    
    section_id: str
    text: str
    level: int
    parent_section_id: Optional[str] = None
    section_number: Optional[str] = None
    subsection: Optional[str] = None
    para_no: Optional[int] = None


class IngestionResult(BaseModel):
    """Statistics and results from ingestion pipeline"""
    
    source_file: str
    status: Literal["success", "partial", "failed"]
    
    # Counts
    total_documents: int = 0
    inserted: int = 0
    skipped: int = 0
    errors: int = 0
    
    # Timing
    start_time: datetime = Field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    
    # Details
    error_messages: List[str] = Field(default_factory=list)
    skipped_ids: List[str] = Field(default_factory=list)
    inserted_ids: List[str] = Field(default_factory=list)
    
    def finalize(self):
        """Mark ingestion as complete and calculate duration"""
        self.end_time = datetime.now()
        self.duration_seconds = (
            self.end_time - self.start_time
        ).total_seconds()
    
    def add_error(self, error: str):
        """Record an error"""
        self.errors += 1
        self.error_messages.append(error)
    
    def add_skip(self, doc_id: str, reason: str):
        """Record a skipped document"""
        self.skipped += 1
        self.skipped_ids.append(doc_id)
        self.error_messages.append(f"Skipped {doc_id}: {reason}")
    
    def add_success(self, doc_id: str):
        """Record successful insertion"""
        self.inserted += 1
        self.inserted_ids.append(doc_id)
    
    def summary(self) -> str:
        """Generate summary string"""
        return (
            f"Ingestion {self.status.upper()}: "
            f"{self.inserted}/{self.total_documents} inserted, "
            f"{self.skipped} skipped, {self.errors} errors "
            f"in {self.duration_seconds:.2f}s"
        )


# ============================================================================
# Configuration Models
# ============================================================================

class ParserConfig(BaseModel):
    """Configuration for document parsers"""
    
    min_paragraph_length: int = Field(
        default=50,
        description="Minimum characters for a valid paragraph"
    )
    max_paragraph_length: int = Field(
        default=10000,
        description="Maximum characters before splitting"
    )
    
    # Statute parsing
    section_pattern: str = Field(
        default=r"(?:Section|Sec\.?)\s+(\d+[A-Z]?)",
        description="Regex for section numbers"
    )
    subsection_pattern: str = Field(
        default=r"\((\d+[a-z]?)\)",
        description="Regex for subsection markers"
    )
    
    # Case parsing
    para_pattern: str = Field(
        default=r"^\s*\[?(\d+)\]?\.?\s",
        description="Regex for paragraph numbers"
    )
    citation_pattern: str = Field(
        default=r"\[(\d{4})\]\s+([A-Z]+)\s+(\d+)",
        description="Regex for case citations"
    )
    
    # Fact extraction (LLM-based)
    extract_facts: bool = Field(
        default=True,
        description="Extract case facts using LLM"
    )
    facts_max_tokens: int = Field(
        default=200,
        description="Max tokens for facts summary"
    )


class IngestionConfig(BaseModel):
    """Configuration for ingestion pipeline"""
    
    batch_size: int = Field(
        default=100,
        ge=1,
        le=1000,
        description="Documents per batch"
    )
    
    allow_duplicates: bool = Field(
        default=False,
        description="Allow duplicate hashes"
    )
    
    skip_existing: bool = Field(
        default=True,
        description="Skip documents that already exist in DB"
    )
    
    parser_config: ParserConfig = Field(
        default_factory=ParserConfig,
        description="Parser configuration"
    )
    
    # Source directories
    statute_dir: str = Field(default="data/statutes/raw")
    case_dir: str = Field(default="data/cases/raw")
    output_dir: str = Field(default="data/processed")
