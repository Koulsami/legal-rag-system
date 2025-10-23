"""
Rule-Based Interpretation Link Extractor

Uses regex patterns to find explicit interpretation relationships.
Expected: 300-500 links with 90%+ precision, confidence 0.8-0.9

Week 2: Extraction Pipeline - Part 2/5
"""

import re
import time
from typing import Dict, List, Optional, Pattern, Tuple

from src.extraction.models import (
    Authority,
    CaseMetadata,
    CaseParagraph,
    ExtractionMethod,
    ExtractionResult,
    InterpretationLink,
    InterpretationType,
    StatuteCitation,
)


# ============================================================================
# INTERPRETATION PATTERNS (Singapore Legal Context)
# ============================================================================

INTERPRETATION_PATTERNS: Dict[str, List[str]] = {
    # Explicit interpretation language
    "explicit": [
        r"(?:held|found|decided|determined)\s+that\s+(?:Section|s\.)\s+(\d+[A-Z]?)",
        r"(?:interpreting|construing|construction of)\s+(?:Section|s\.)\s+(\d+[A-Z]?)",
        r"(?:interpretation|meaning|scope)\s+of\s+(?:Section|s\.)\s+(\d+[A-Z]?)",
        r"(?:Section|s\.)\s+(\d+[A-Z]?)\s+(?:means|requires|provides|applies)",
        r"(?:Section|s\.)\s+(\d+[A-Z]?)\s+to\s+mean",
    ],
    
    # Narrow interpretation markers
    "narrow": [
        r"narrow(?:ly)?\s+(?:interpreted|construed|read)",
        r"(?:only|solely|merely)\s+applies\s+(?:to|where|when)",
        r"does\s+not\s+extend\s+to",
        r"limited\s+to",
        r"confined\s+to",
        r"restricted\s+to",
    ],
    
    # Broad interpretation markers
    "broad": [
        r"broad(?:ly)?\s+(?:interpreted|construed|read)",
        r"not\s+(?:limited|confined|restricted)\s+to",
        r"includes?\s+(?:not\s+only|also)",
        r"(?:wide|expansive|liberal)\s+(?:interpretation|reading|construction)",
    ],
    
    # Clarification markers
    "clarify": [
        r"clarif(?:y|ies|ied)",
        r"(?:explained|elaborated)\s+(?:in|that)",
        r"to\s+be\s+understood\s+as",
        r"what\s+(?:is|was)\s+meant\s+by",
    ],
    
    # Purposive interpretation
    "purposive": [
        r"purposive\s+(?:interpretation|approach|construction)",
        r"legislative\s+(?:intent|purpose|object)",
        r"(?:object|purpose)\s+(?:of|and\s+purpose)",
        r"mischief\s+(?:rule|which)",
        r"Parliament\s+(?:intended|meant)",
    ],
    
    # Literal interpretation
    "literal": [
        r"literal\s+(?:interpretation|reading|meaning)",
        r"plain\s+(?:meaning|text|words?)",
        r"natural\s+(?:meaning|interpretation)",
        r"ordinary\s+meaning",
    ],
}


# Singapore statute citation patterns
STATUTE_CITATION_PATTERN = re.compile(
    r"""
    (?P<name>
        (?:[A-Z][a-z]+\s+)*                    # Multi-word statute names
        (?:Act|Rules?|Order|Code|Ordinance)    # Statute type
    )
    \s+
    (?:
        \(Cap\s*\.?\s*(?P<chapter>\d+[A-Z]?)\) |  # Chapter number
        \((?P<year>\d{4})\)                       # Year
    )?
    \s*
    (?:
        (?:Section|s\.|sec\.)\s*(?P<section>\d+[A-Z]?(?:\([^)]+\))?)  # Section
    )?
    """,
    re.VERBOSE | re.IGNORECASE
)


# ============================================================================
# STATUTE CITATION EXTRACTOR
# ============================================================================

class StatuteCitationExtractor:
    """Extract statute citations from text"""
    
    def __init__(self):
        self.pattern = STATUTE_CITATION_PATTERN
        
    def extract(self, text: str) -> List[StatuteCitation]:
        """
        Find all statute citations in text
        
        Returns:
            List of parsed statute citations
        """
        citations = []
        
        for match in self.pattern.finditer(text):
            name = match.group('name').strip()
            section = match.group('section')
            chapter = match.group('chapter')
            year = match.group('year')
            
            # Skip if no statute name
            if not name:
                continue
            
            citation = StatuteCitation(
                name=name,
                section=section or "",
                full_text=match.group(0).strip()
            )
            citations.append(citation)
        
        return citations


# ============================================================================
# INTERPRETATION TYPE CLASSIFIER
# ============================================================================

class InterpretationTypeClassifier:
    """Classify interpretation type from paragraph text"""
    
    def __init__(self):
        self.patterns = self._compile_patterns()
    
    def _compile_patterns(self) -> Dict[InterpretationType, List[Pattern]]:
        """Compile regex patterns for each type"""
        compiled = {}
        
        for pattern_type, pattern_list in INTERPRETATION_PATTERNS.items():
            interp_type = self._map_pattern_type(pattern_type)
            compiled[interp_type] = [
                re.compile(p, re.IGNORECASE) for p in pattern_list
            ]
        
        return compiled
    
    def _map_pattern_type(self, pattern_type: str) -> InterpretationType:
        """Map pattern category to InterpretationType"""
        mapping = {
            "explicit": InterpretationType.CLARIFY,
            "narrow": InterpretationType.NARROW,
            "broad": InterpretationType.BROAD,
            "clarify": InterpretationType.CLARIFY,
            "purposive": InterpretationType.PURPOSIVE,
            "literal": InterpretationType.LITERAL,
        }
        return mapping.get(pattern_type, InterpretationType.CLARIFY)
    
    def classify(self, text: str) -> Tuple[InterpretationType, float]:
        """
        Classify interpretation type
        
        Returns:
            (InterpretationType, confidence_score)
        """
        scores: Dict[InterpretationType, int] = {}
        
        # Count pattern matches for each type
        for interp_type, patterns in self.patterns.items():
            count = sum(1 for p in patterns if p.search(text))
            if count > 0:
                scores[interp_type] = count
        
        if not scores:
            return InterpretationType.CLARIFY, 0.5
        
        # Return type with most matches
        best_type = max(scores, key=scores.get)
        confidence = min(0.8 + (scores[best_type] * 0.05), 0.95)
        
        return best_type, confidence


# ============================================================================
# AUTHORITY LEVEL DETERMINER
# ============================================================================

class AuthorityDeterminer:
    """Determine authority level of interpretation"""
    
    # Singapore court hierarchy
    BINDING_COURTS = {"SGCA", "CA"}  # Court of Appeal
    PERSUASIVE_COURTS = {"SGHC", "HC", "SGDC", "DC"}  # High Court, District Court
    
    def determine(
        self,
        case_metadata: CaseMetadata,
        paragraph_text: str
    ) -> Tuple[Authority, float]:
        """
        Determine authority level
        
        Returns:
            (Authority, boost_factor)
        """
        court = case_metadata.court.upper()
        
        # Check for obiter/dissent markers
        if self._is_obiter(paragraph_text):
            return Authority.OBITER, 1.5
        
        if self._is_dissent(paragraph_text):
            return Authority.DISSENT, 1.2
        
        # Authority by court level
        if court in self.BINDING_COURTS:
            return Authority.BINDING, 2.8
        elif court in self.PERSUASIVE_COURTS:
            return Authority.PERSUASIVE, 2.0
        else:
            return Authority.PERSUASIVE, 1.5
    
    def _is_obiter(self, text: str) -> bool:
        """Check if paragraph contains obiter dicta markers"""
        obiter_markers = [
            r"obiter\s+dict(?:um|a)",
            r"by\s+the\s+way",
            r"in\s+passing",
        ]
        return any(re.search(m, text, re.IGNORECASE) for m in obiter_markers)
    
    def _is_dissent(self, text: str) -> bool:
        """Check if paragraph is from dissenting opinion"""
        dissent_markers = [
            r"dissenting",
            r"in\s+dissent",
            r"I\s+would\s+(?:respectfully\s+)?disagree",
        ]
        return any(re.search(m, text, re.IGNORECASE) for m in dissent_markers)


# ============================================================================
# HOLDING EXTRACTOR
# ============================================================================

class HoldingExtractor:
    """Extract holding statement from paragraph"""
    
    def extract(self, text: str, statute_cite: StatuteCitation) -> str:
        """
        Extract 1-2 sentence holding about statute
        
        Strategy:
        1. Find sentence mentioning statute
        2. Extract sentence + next sentence
        3. Truncate if too long
        """
        sentences = self._split_sentences(text)
        
        # Find first sentence mentioning statute
        statute_keywords = [statute_cite.name, statute_cite.section]
        for i, sent in enumerate(sentences):
            if any(kw.lower() in sent.lower() for kw in statute_keywords if kw):
                # Take this sentence + next one
                holding_sentences = sentences[i:i+2]
                holding = " ".join(holding_sentences)
                
                # Truncate if too long (max 300 chars)
                if len(holding) > 300:
                    holding = holding[:297] + "..."
                
                return holding.strip()
        
        # Fallback: first 2 sentences
        return " ".join(sentences[:2])[:300]
    
    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences (simple version)"""
        # Simple sentence splitter
        sentences = re.split(r'[.!?]+\s+', text)
        return [s.strip() for s in sentences if s.strip()]


# ============================================================================
# RULE-BASED EXTRACTOR (MAIN CLASS)
# ============================================================================

class RuleBasedExtractor:
    """
    Extract interpretation links using regex patterns
    
    Expected Performance:
    - Precision: 90%+
    - Recall: 60-70%
    - Output: 300-500 links from 1000-5000 cases
    """
    
    def __init__(self):
        self.citation_extractor = StatuteCitationExtractor()
        self.type_classifier = InterpretationTypeClassifier()
        self.authority_determiner = AuthorityDeterminer()
        self.holding_extractor = HoldingExtractor()
        
        # Cache for performance
        self._statute_id_cache: Dict[str, str] = {}
    
    def extract(
        self,
        case_paragraphs: List[CaseParagraph],
        verbose: bool = False
    ) -> ExtractionResult:
        """
        Extract interpretation links from case paragraphs
        
        Args:
            case_paragraphs: List of case paragraphs to process
            verbose: Print progress
            
        Returns:
            ExtractionResult with extracted links and metrics
        """
        start_time = time.time()
        links: List[InterpretationLink] = []
        cases_processed = set()
        
        for para in case_paragraphs:
            cases_processed.add(para.case_metadata.doc_id)
            
            # Find statute citations
            statute_cites = self.citation_extractor.extract(para.text)
            if not statute_cites:
                continue
            
            # Check for interpretation patterns
            if not self._has_interpretation_pattern(para.text):
                continue
            
            # Process each statute citation
            for cite in statute_cites:
                link = self._create_link(para, cite)
                if link:
                    links.append(link)
                    
                    if verbose and len(links) % 50 == 0:
                        print(f"Extracted {len(links)} links...")
        
        duration = time.time() - start_time
        
        return ExtractionResult(
            links=links,
            total_cases_processed=len(cases_processed),
            total_paragraphs_scanned=len(case_paragraphs),
            extraction_method=ExtractionMethod.RULE_BASED,
            duration_seconds=duration
        )
    
    def _has_interpretation_pattern(self, text: str) -> bool:
        """Check if text contains any interpretation pattern"""
        for patterns in INTERPRETATION_PATTERNS.values():
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    return True
        return False
    
    def _create_link(
        self,
        para: CaseParagraph,
        statute_cite: StatuteCitation
    ) -> Optional[InterpretationLink]:
        """Create interpretation link from paragraph and citation"""
        
        # Classify interpretation type
        interp_type, type_confidence = self.type_classifier.classify(para.text)
        
        # Determine authority level
        authority, boost_factor = self.authority_determiner.determine(
            para.case_metadata,
            para.text
        )
        
        # Extract holding
        holding = self.holding_extractor.extract(para.text, statute_cite)
        
        # Generate IDs
        statute_id = self._generate_statute_id(statute_cite)
        case_id = para.paragraph_id
        
        # Create link
        link = InterpretationLink(
            statute_id=statute_id,
            case_id=case_id,
            statute_name=statute_cite.name,
            statute_section=statute_cite.section,
            statute_text=statute_cite.full_text,
            case_name=para.case_metadata.case_name,
            case_citation=para.case_metadata.citation,
            case_para_no=para.para_no,
            case_text=para.text,
            court=para.case_metadata.court,
            year=para.case_metadata.year,
            interpretation_type=interp_type,
            authority=authority,
            holding=holding,
            extraction_method=ExtractionMethod.RULE_BASED,
            confidence=type_confidence,
            boost_factor=boost_factor,
        )
        
        return link
    
    def _generate_statute_id(self, cite: StatuteCitation) -> str:
        """Generate unique statute ID"""
        # Normalize statute name
        name_normalized = cite.name.lower().replace(" ", "_")
        section_normalized = cite.section.replace("(", "").replace(")", "").replace(" ", "")
        
        statute_id = f"sg_statute_{name_normalized}"
        if section_normalized:
            statute_id += f"_s{section_normalized}"
        
        return statute_id


# ============================================================================
# USAGE EXAMPLE
# ============================================================================

if __name__ == "__main__":
    # Example usage
    from datetime import datetime
    
    # Create sample case paragraph
    sample_para = CaseParagraph(
        para_no=158,
        text="""
        The Court held that Section 2 of the Misrepresentation Act applies only 
        where there exists a fiduciary relationship or special knowledge on the part 
        of the defendant. The scope of the duty to disclose is therefore narrowly 
        construed and does not extend to arm's length commercial transactions.
        """,
        case_metadata=CaseMetadata(
            doc_id="sg_case_2013_sgca_36",
            case_name="Wee Chiaw Sek Anna v Ng Li-Ann Genevieve",
            citation="[2013] SGCA 36",
            court="SGCA",
            year=2013
        )
    )
    
    # Extract links
    extractor = RuleBasedExtractor()
    result = extractor.extract([sample_para], verbose=True)
    
    print(result.summary())
    
    if result.links:
        print("\nFirst Link:")
        link = result.links[0]
        print(f"Statute: {link.statute_id}")
        print(f"Case: {link.case_id}")
        print(f"Type: {link.interpretation_type.value}")
        print(f"Authority: {link.authority.value}")
        print(f"Confidence: {link.confidence:.2f}")
        print(f"Holding: {link.holding}")
