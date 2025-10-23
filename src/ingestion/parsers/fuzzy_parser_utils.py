"""
Fuzzy matching utilities for legal document parsing.
Handles OCR errors, spacing variations, and format inconsistencies.
"""

from typing import List, Tuple, Optional
import re
from dataclasses import dataclass
from rapidfuzz import fuzz


@dataclass
class FuzzyMatch:
    """Represents a fuzzy match result."""
    number: str  # Section/paragraph number
    text: str  # Full text of the section/paragraph
    start_pos: int  # Character position in document
    end_pos: int  # End position
    confidence: float  # 0.0 to 1.0
    match_type: str  # "exact", "fuzzy", "heuristic"


class FuzzyStatuteMatcher:
    """
    Fuzzy matcher for statute sections.
    
    Handles variations like:
    - "1.Where" (standard)
    - "1 .Where" (space before dot)
    - "1. Where" (space after dot)
    - "1Where" (missing dot)
    - "Section 1." (with label)
    """
    
    def __init__(self, similarity_threshold: int = 80):
        """
        Args:
            similarity_threshold: Minimum similarity score (0-100) for fuzzy matches
        """
        self.threshold = similarity_threshold
        
        # Multiple patterns to try
        self.patterns = [
            # Standard: "1.Where"
            (re.compile(r'^\s*(\d+[A-Z]?)\.(?:—)?(?:\(\d+\))?\s*([A-Z][^.]*)', re.MULTILINE), 1.0),
            # With space before dot: "1 .Where"
            (re.compile(r'^\s*(\d+[A-Z]?)\s+\.(?:—)?(?:\(\d+\))?\s*([A-Z][^.]*)', re.MULTILINE), 0.95),
            # With section label: "Section 1."
            (re.compile(r'^\s*(?:Section|Sec\.?)\s+(\d+[A-Z]?)\.?\s*([A-Z][^.]*)', re.MULTILINE), 0.9),
            # Dot with extra space: "1. Where"
            (re.compile(r'^\s*(\d+[A-Z]?)\.\s{2,}([A-Z][^.]*)', re.MULTILINE), 0.9),
            # No dot, just number: "1 Where"
            (re.compile(r'^\s*(\d+[A-Z]?)\s+([A-Z][^.]{20,})', re.MULTILINE), 0.85),
        ]
    
    def find_sections(self, text: str) -> List[FuzzyMatch]:
        """
        Find all sections in text using fuzzy matching.
        
        Returns:
            List of FuzzyMatch objects, sorted by position
        """
        best_matches = []
        best_confidence = 0.0
        
        # Try each pattern, keep the one with best results
        for pattern, base_confidence in self.patterns:
            matches = self._extract_with_pattern(text, pattern, base_confidence)
            
            if matches:
                # Calculate overall confidence based on match quality
                avg_confidence = sum(m.confidence for m in matches) / len(matches)
                
                # Bonus for sequential numbering
                if self._is_sequential([int(re.match(r'\d+', m.number).group()) for m in matches]):
                    avg_confidence += 0.1
                
                # Keep best result
                if avg_confidence > best_confidence:
                    best_matches = matches
                    best_confidence = avg_confidence
        
        # If no patterns worked, try heuristic line-by-line search
        if not best_matches:
            best_matches = self._heuristic_search(text)
        
        return best_matches
    
    def _extract_with_pattern(
        self, 
        text: str, 
        pattern: re.Pattern, 
        base_confidence: float
    ) -> List[FuzzyMatch]:
        """Extract matches using a specific regex pattern."""
        matches = list(pattern.finditer(text))
        
        if not matches:
            return []
        
        results = []
        for i, match in enumerate(matches):
            section_num = match.group(1)
            
            # Extract section text
            start_pos = match.start()
            end_pos = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            section_text = text[start_pos:end_pos].strip()
            
            # Skip if too short (likely false positive)
            if len(section_text) < 50:
                continue
            
            results.append(FuzzyMatch(
                number=section_num,
                text=section_text,
                start_pos=start_pos,
                end_pos=end_pos,
                confidence=base_confidence,
                match_type="exact" if base_confidence >= 0.95 else "fuzzy"
            ))
        
        return results
    
    def _heuristic_search(self, text: str) -> List[FuzzyMatch]:
        """
        Heuristic-based search when regex fails.
        
        Looks for lines that:
        1. Start with a number
        2. Have substantial text after (>100 chars to next similar line)
        3. Are roughly sequential
        """
        lines = text.split('\n')
        potential_sections = []
        
        for i, line in enumerate(lines):
            line = line.strip()
            
            # Must start with 1-3 digits
            if not re.match(r'^\d{1,3}', line):
                continue
            
            # Extract number
            num_match = re.match(r'^(\d+[A-Z]?)[\s\.\—]+(.+)', line)
            if not num_match:
                continue
            
            section_num = num_match.group(1)
            
            # Calculate end position (next section or end of text)
            start_line_idx = i
            end_line_idx = i + 1
            
            # Look ahead to find next section
            for j in range(i + 1, min(i + 50, len(lines))):
                if re.match(r'^\d{1,3}[\s\.\—]', lines[j].strip()):
                    end_line_idx = j
                    break
            
            section_text = '\n'.join(lines[start_line_idx:end_line_idx])
            
            # Must be substantial
            if len(section_text) < 100:
                continue
            
            # Find position in original text
            start_pos = text.find(section_text)
            if start_pos == -1:
                continue
            
            potential_sections.append(FuzzyMatch(
                number=section_num,
                text=section_text.strip(),
                start_pos=start_pos,
                end_pos=start_pos + len(section_text),
                confidence=0.7,
                match_type="heuristic"
            ))
        
        # Filter: keep only if roughly sequential
        if potential_sections:
            numbers = [int(re.match(r'\d+', s.number).group()) for s in potential_sections]
            if self._is_roughly_sequential(numbers):
                return potential_sections
        
        return []
    
    def _is_sequential(self, numbers: List[int]) -> bool:
        """Check if numbers are perfectly sequential (1,2,3,4,...)."""
        if not numbers:
            return False
        return numbers == list(range(numbers[0], numbers[0] + len(numbers)))
    
    def _is_roughly_sequential(self, numbers: List[int]) -> bool:
        """Check if numbers are mostly sequential (allow a few gaps)."""
        if len(numbers) < 2:
            return False
        
        gaps = [numbers[i+1] - numbers[i] for i in range(len(numbers)-1)]
        # Most gaps should be 1, allow some 2s or 3s
        return sum(1 for g in gaps if g <= 3) / len(gaps) > 0.7


class FuzzyCaseMatcher:
    """
    Fuzzy matcher for case paragraphs.
    
    Handles variations like:
    - "1          Text" (multiple spaces)
    - "1     Text" (fewer spaces)
    - "1\tText" (tabs)
    - "1. Text" (with dot)
    - "[1] Text" (with brackets)
    """
    
    def __init__(self, similarity_threshold: int = 80):
        self.threshold = similarity_threshold
        
        # Multiple patterns to try
        self.patterns = [
            # Standard: number + 2+ spaces
            (re.compile(r'^\s*(\d+)\s{2,}([A-Z].+)', re.MULTILINE), 1.0),
            # With tab
            (re.compile(r'^\s*(\d+)\t+([A-Z].+)', re.MULTILINE), 0.95),
            # With dot + spaces
            (re.compile(r'^\s*(\d+)\.\s+([A-Z].+)', re.MULTILINE), 0.9),
            # With brackets [1]
            (re.compile(r'^\s*\[(\d+)\]\s+([A-Z].+)', re.MULTILINE), 0.95),
            # Just one space (less reliable)
            (re.compile(r'^\s*(\d+)\s([A-Z][^0-9]{30,})', re.MULTILINE), 0.8),
        ]
    
    def find_paragraphs(self, text: str) -> List[FuzzyMatch]:
        """
        Find all paragraphs in text using fuzzy matching.
        
        Returns:
            List of FuzzyMatch objects, sorted by position
        """
        best_matches = []
        best_confidence = 0.0
        
        # Try each pattern
        for pattern, base_confidence in self.patterns:
            matches = self._extract_with_pattern(text, pattern, base_confidence)
            
            if matches:
                # Calculate overall confidence
                avg_confidence = sum(m.confidence for m in matches) / len(matches)
                
                # Bonus for sequential numbering
                if self._is_sequential([int(m.number) for m in matches]):
                    avg_confidence += 0.1
                
                # Keep best result
                if avg_confidence > best_confidence:
                    best_matches = matches
                    best_confidence = avg_confidence
        
        # Heuristic fallback
        if not best_matches:
            best_matches = self._heuristic_search(text)
        
        return best_matches
    
    def _extract_with_pattern(
        self, 
        text: str, 
        pattern: re.Pattern, 
        base_confidence: float
    ) -> List[FuzzyMatch]:
        """Extract matches using a specific regex pattern."""
        matches = list(pattern.finditer(text))
        
        if not matches:
            return []
        
        results = []
        for i, match in enumerate(matches):
            para_num = match.group(1)
            
            # Extract paragraph text
            start_pos = match.start()
            end_pos = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            para_text = text[start_pos:end_pos].strip()
            
            # Remove paragraph marker from text
            para_text = re.sub(r'^\s*\[?\d+\]?[\s\.\t]+', '', para_text)
            
            # Skip if too short
            if len(para_text) < 30:
                continue
            
            results.append(FuzzyMatch(
                number=para_num,
                text=para_text,
                start_pos=start_pos,
                end_pos=end_pos,
                confidence=base_confidence,
                match_type="exact" if base_confidence >= 0.95 else "fuzzy"
            ))
        
        return results
    
    def _heuristic_search(self, text: str) -> List[FuzzyMatch]:
        """
        Heuristic-based search for paragraphs.
        
        More aggressive than statute search since paragraphs
        can have more format variations.
        """
        lines = text.split('\n')
        potential_paragraphs = []
        
        for i, line in enumerate(lines):
            line = line.strip()
            
            # Must start with 1-4 digits
            if not re.match(r'^\[?\d{1,4}\]?', line):
                continue
            
            # Extract number (with or without brackets)
            num_match = re.match(r'^\[?(\d+)\]?[\s\.\—\t]+(.+)', line)
            if not num_match:
                continue
            
            para_num = num_match.group(1)
            
            # Calculate end position
            start_line_idx = i
            end_line_idx = i + 1
            
            # Look ahead to find next paragraph
            for j in range(i + 1, min(i + 30, len(lines))):
                if re.match(r'^\[?\d{1,4}\]?[\s\.\—\t]', lines[j].strip()):
                    end_line_idx = j
                    break
            
            para_text = '\n'.join(lines[start_line_idx:end_line_idx])
            
            # Must be substantial (but shorter than sections)
            if len(para_text) < 30:
                continue
            
            # Find position
            start_pos = text.find(para_text)
            if start_pos == -1:
                continue
            
            # Clean text
            cleaned_text = re.sub(r'^\[?\d+\]?[\s\.\—\t]+', '', para_text.strip())
            
            potential_paragraphs.append(FuzzyMatch(
                number=para_num,
                text=cleaned_text,
                start_pos=start_pos,
                end_pos=start_pos + len(para_text),
                confidence=0.7,
                match_type="heuristic"
            ))
        
        # Filter: keep only if roughly sequential
        if potential_paragraphs:
            numbers = [int(p.number) for p in potential_paragraphs]
            if self._is_roughly_sequential(numbers):
                return potential_paragraphs
        
        return []
    
    def _is_sequential(self, numbers: List[int]) -> bool:
        """Check if numbers are perfectly sequential."""
        if not numbers:
            return False
        return numbers == list(range(numbers[0], numbers[0] + len(numbers)))
    
    def _is_roughly_sequential(self, numbers: List[int]) -> bool:
        """Check if numbers are mostly sequential."""
        if len(numbers) < 3:  # Need at least 3 paragraphs
            return False
        
        # Check if sorted
        if numbers != sorted(numbers):
            return False
        
        # Check gaps
        gaps = [numbers[i+1] - numbers[i] for i in range(len(numbers)-1)]
        # Most gaps should be 1 or 2
        return sum(1 for g in gaps if g <= 2) / len(gaps) > 0.7
