"""
Data models for extraction pipeline.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional
from uuid import UUID, uuid4


class InterpretationType(str, Enum):
    """Types of statutory interpretation"""
    NARROW = "NARROW"
    BROAD = "BROAD"
    CLARIFY = "CLARIFY"
    PURPOSIVE = "PURPOSIVE"
    LITERAL = "LITERAL"
    APPLY = "APPLY"


class Authority(str, Enum):
    """Authority level"""
    BINDING = "BINDING"
    PERSUASIVE = "PERSUASIVE"
    OBITER = "OBITER"
    DISSENT = "DISSENT"


class ExtractionMethod(str, Enum):
    """Extraction method"""
    RULE_BASED = "RULE_BASED"
    LLM_ASSISTED = "LLM_ASSISTED"
    MANUAL = "MANUAL"


@dataclass
class CaseMetadata:
    """Case document metadata"""
    doc_id: str
    case_name: str
    citation: str
    court: str
    year: int
    jurisdiction: str = "SG"


@dataclass
class CaseParagraph:
    """Single paragraph from a case"""
    para_no: int
    text: str
    case_metadata: CaseMetadata
    
    @property
    def paragraph_id(self) -> str:
        return f"{self.case_metadata.doc_id}_para_{self.para_no}"


@dataclass
class StatuteCitation:
    """Parsed statute citation"""
    name: str
    section: str
    subsection: Optional[str] = None
    full_text: str = ""


@dataclass
class CaseParagraphInput:
    """Input: Case paragraph for extraction"""
    doc_id: str
    para_no: int
    text: str
    case_name: str
    citation: str
    court: str
    year: int
    
    @property
    def paragraph_id(self) -> str:
        return f"{self.doc_id}_para_{self.para_no}"


@dataclass
class InterpretationLink:
    """Output: Extracted interpretation link"""
    id: UUID = field(default_factory=uuid4)
    statute_id: str = ""
    case_id: str = ""
    statute_name: str = ""
    statute_section: str = ""
    statute_text: str = ""
    case_name: str = ""
    case_citation: str = ""
    case_para_no: int = 0
    case_text: str = ""
    court: str = ""
    year: int = 0
    interpretation_type: InterpretationType = InterpretationType.CLARIFY
    authority: Authority = Authority.PERSUASIVE
    holding: str = ""
    extraction_method: ExtractionMethod = ExtractionMethod.RULE_BASED
    confidence: float = 0.0
    boost_factor: float = 2.0
    
    def __post_init__(self):
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"Confidence must be 0-1, got {self.confidence}")
        if not 1.0 <= self.boost_factor <= 5.0:
            raise ValueError(f"Boost factor must be 1-5, got {self.boost_factor}")
    
    def to_dict(self) -> Dict:
        return {
            "statute_id": self.statute_id,
            "case_id": self.case_id,
            "interpretation_type": self.interpretation_type.value,
            "authority": self.authority.value,
        }


@dataclass  
class ExtractionResult:
    """Result of extraction pipeline"""
    links: List[InterpretationLink]
    total_cases_processed: int
    total_paragraphs_scanned: int
    extraction_method: ExtractionMethod
    duration_seconds: float
    avg_confidence: float = 0.0
    
    def __post_init__(self):
        if self.links:
            self.avg_confidence = sum(l.confidence for l in self.links) / len(self.links)
    
    def summary(self) -> str:
        return f"""
Extraction Summary ({self.extraction_method.value})
{'=' * 60}
Total Links: {len(self.links)}
Cases Processed: {self.total_cases_processed}
Paragraphs Scanned: {self.total_paragraphs_scanned}
Average Confidence: {self.avg_confidence:.2f}
Duration: {self.duration_seconds:.1f}s
        """.strip()


@dataclass
class ValidationCheck:
    """Single validation check result"""
    check_name: str
    passed: bool
    details: str = ""


@dataclass
class LinkQualityScore:
    """Quality score for extracted link"""
    link: InterpretationLink
    score: float
    checks: List[ValidationCheck]
    passed: bool
