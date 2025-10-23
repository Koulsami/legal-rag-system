"""
Text processing utilities for document ingestion.

Functions for:
- Text normalization
- Paragraph segmentation
- Section detection
- Citation extraction
"""

import re
from typing import List, Tuple, Optional
import hashlib


# ============================================================================
# Text Normalization
# ============================================================================

def normalize_text(text: str) -> str:
    """
    Normalize text by removing extra whitespace and fixing encoding issues.
    
    Args:
        text: Raw text
        
    Returns:
        Normalized text
    """
    if not text:
        return ""
    
    # Fix common encoding issues
    text = text.replace('\r\n', '\n')  # Windows line endings
    text = text.replace('\r', '\n')    # Old Mac line endings
    text = text.replace('\u00a0', ' ') # Non-breaking space
    text = text.replace('\u2019', "'") # Smart apostrophe
    text = text.replace('\u201c', '"') # Smart quote left
    text = text.replace('\u201d', '"') # Smart quote right
    text = text.replace('\u2013', '-') # En dash
    text = text.replace('\u2014', '-') # Em dash
    
    # Remove zero-width characters
    text = text.replace('\u200b', '')  # Zero-width space
    text = text.replace('\ufeff', '')  # Zero-width no-break space
    
    # Normalize whitespace
    text = re.sub(r'[ \t]+', ' ', text)  # Multiple spaces to single
    text = re.sub(r'\n\n\n+', '\n\n', text)  # Max 2 newlines
    
    return text.strip()


def clean_paragraph(text: str) -> str:
    """
    Clean a single paragraph.
    
    Args:
        text: Paragraph text
        
    Returns:
        Cleaned text
    """
    text = normalize_text(text)
    
    # Remove paragraph numbers/markers at start
    text = re.sub(r'^\s*\[?\d+\]?\.?\s*', '', text)
    
    # Remove excessive periods (often from redacted text)
    text = re.sub(r'\.{4,}', '...', text)
    
    return text.strip()


def generate_hash(text: str) -> str:
    """
    Generate SHA-256 hash of text for deduplication.
    
    Args:
        text: Text to hash
        
    Returns:
        Hexadecimal hash string
    """
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


# ============================================================================
# Paragraph Segmentation
# ============================================================================

def split_into_paragraphs(
    text: str,
    min_length: int = 50,
    max_length: int = 10000
) -> List[str]:
    """
    Split text into paragraphs based on line breaks.
    
    Args:
        text: Full document text
        min_length: Minimum paragraph length (characters)
        max_length: Maximum paragraph length (characters)
        
    Returns:
        List of paragraph texts
    """
    # Split on double newlines (standard paragraph separator)
    paragraphs = text.split('\n\n')
    
    result = []
    current_para = ""
    
    for para in paragraphs:
        para = para.strip()
        
        if not para:
            continue
        
        # If adding this para would exceed max_length, save current and start new
        if current_para and len(current_para) + len(para) > max_length:
            if len(current_para) >= min_length:
                result.append(current_para)
            current_para = para
        else:
            # Accumulate paragraphs
            if current_para:
                current_para += "\n\n" + para
            else:
                current_para = para
    
    # Add final paragraph
    if current_para and len(current_para) >= min_length:
        result.append(current_para)
    
    return result


def segment_by_paragraph_numbers(text: str) -> List[Tuple[int, str]]:
    """
    Segment text by explicit paragraph numbers like [1], [2], etc.
    
    Args:
        text: Full document text
        
    Returns:
        List of (paragraph_number, text) tuples
    """
    # Pattern for paragraph numbers: [1], [2], etc.
    pattern = r'\[(\d+)\]\s*'
    
    segments = []
    current_para_no = None
    current_text = []
    
    lines = text.split('\n')
    
    for line in lines:
        match = re.match(pattern, line)
        
        if match:
            # Save previous paragraph
            if current_para_no is not None and current_text:
                para_text = '\n'.join(current_text).strip()
                if para_text:
                    segments.append((current_para_no, para_text))
            
            # Start new paragraph
            current_para_no = int(match.group(1))
            # Remove paragraph number from line
            line = re.sub(pattern, '', line, count=1)
            current_text = [line] if line.strip() else []
        else:
            # Continue current paragraph
            if current_para_no is not None:
                current_text.append(line)
    
    # Add final paragraph
    if current_para_no is not None and current_text:
        para_text = '\n'.join(current_text).strip()
        if para_text:
            segments.append((current_para_no, para_text))
    
    return segments


# ============================================================================
# Section Detection
# ============================================================================

def extract_section_number(text: str) -> Optional[str]:
    """
    Extract section number from text.
    
    Patterns supported:
    - "Section 2"
    - "Sec. 2"
    - "s 2"
    - "s. 2"
    - "Section 2A"
    
    Args:
        text: Text containing section reference
        
    Returns:
        Section number or None
    """
    patterns = [
        r'(?:Section|Sec\.?|s\.?)\s+(\d+[A-Z]?)',
        r'^(\d+[A-Z]?)\.\s',  # "2. Title" format
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1)
    
    return None


def extract_subsection_marker(text: str) -> Optional[str]:
    """
    Extract subsection marker from text.
    
    Patterns: (1), (2), (a), (b), etc.
    
    Args:
        text: Text containing subsection marker
        
    Returns:
        Subsection marker or None
    """
    match = re.search(r'^\s*\(([0-9a-z]+)\)', text)
    if match:
        return match.group(1)
    return None


def detect_hierarchy_level(text: str, parent_level: int = 0) -> int:
    """
    Detect hierarchy level based on text formatting.
    
    Args:
        text: Text to analyze
        parent_level: Level of parent document
        
    Returns:
        Detected level (0-5)
    """
    text = text.strip()
    
    # Root level: Usually all caps or has "ACT" in title
    if parent_level == 0:
        if 'ACT' in text.upper() or text.isupper():
            return 0
        elif extract_section_number(text):
            return 1
        elif extract_subsection_marker(text):
            return 2
    
    # Subsection level
    elif parent_level == 1:
        if extract_subsection_marker(text):
            return 2
        else:
            return 1
    
    # Sub-subsection level
    elif parent_level == 2:
        return 3
    
    # Default: one level below parent
    return parent_level + 1


# ============================================================================
# Citation Extraction
# ============================================================================

def extract_citation(text: str) -> Optional[str]:
    """
    Extract legal citation from text.
    
    Patterns supported:
    - [2020] SGCA 36
    - [2020] SGHC 100
    - [2020] 1 SLR 123
    
    Args:
        text: Text containing citation
        
    Returns:
        Citation string or None
    """
    # Singapore case citation pattern
    pattern = r'\[(\d{4})\]\s+(\d+\s+)?([A-Z]+)\s+(\d+)'
    
    match = re.search(pattern, text)
    if match:
        year = match.group(1)
        volume = match.group(2).strip() if match.group(2) else ""
        court = match.group(3)
        number = match.group(4)
        
        if volume:
            return f"[{year}] {volume} {court} {number}"
        else:
            return f"[{year}] {court} {number}"
    
    return None


def extract_court_from_citation(citation: str) -> Optional[str]:
    """
    Extract court abbreviation from citation.
    
    Args:
        citation: Citation string
        
    Returns:
        Court abbreviation (SGCA, SGHC, etc.) or None
    """
    match = re.search(r'\[(\d{4})\]\s+(?:\d+\s+)?([A-Z]+)', citation)
    if match:
        return match.group(2)
    return None


def extract_year_from_citation(citation: str) -> Optional[int]:
    """
    Extract year from citation.
    
    Args:
        citation: Citation string
        
    Returns:
        Year as integer or None
    """
    match = re.search(r'\[(\d{4})\]', citation)
    if match:
        return int(match.group(1))
    return None


# ============================================================================
# Document ID Generation
# ============================================================================

def generate_statute_id(
    act_name: str,
    section_number: Optional[str] = None,
    subsection: Optional[str] = None
) -> str:
    """
    Generate unique ID for statute document.
    
    Format: sg_statute_{act}_{section}_{subsection}
    
    Args:
        act_name: Name of act
        section_number: Section number
        subsection: Subsection marker
        
    Returns:
        Document ID
    """
    # Normalize act name
    act_slug = act_name.lower()
    act_slug = re.sub(r'[^\w\s-]', '', act_slug)
    act_slug = re.sub(r'[-\s]+', '_', act_slug)
    act_slug = act_slug[:50]  # Limit length
    
    parts = ['sg', 'statute', act_slug]
    
    if section_number:
        parts.append(f"s{section_number}")
    
    if subsection:
        parts.append(subsection)
    
    return '_'.join(parts)


def generate_case_id(
    citation: str,
    para_no: Optional[int] = None
) -> str:
    """
    Generate unique ID for case document.
    
    Format: sg_case_{year}_{court}_{number}_para_{para_no}
    
    Args:
        citation: Case citation
        para_no: Paragraph number
        
    Returns:
        Document ID
    """
    # Extract components
    match = re.search(r'\[(\d{4})\]\s+(?:\d+\s+)?([A-Z]+)\s+(\d+)', citation)
    
    if not match:
        # Fallback: use hash of citation
        hash_part = hashlib.md5(citation.encode()).hexdigest()[:8]
        base_id = f"sg_case_{hash_part}"
    else:
        year = match.group(1)
        court = match.group(2).lower()
        number = match.group(3)
        base_id = f"sg_case_{year}_{court}_{number}"
    
    if para_no:
        return f"{base_id}_para_{para_no}"
    
    return base_id


# ============================================================================
# Title Extraction
# ============================================================================

def extract_title_from_text(text: str, max_length: int = 200) -> str:
    """
    Extract title from beginning of text.
    
    Args:
        text: Document text
        max_length: Maximum title length
        
    Returns:
        Extracted title
    """
    # Take first line or first sentence
    lines = text.split('\n')
    first_line = lines[0].strip() if lines else ""
    
    if len(first_line) <= max_length:
        return first_line
    
    # Try first sentence
    match = re.match(r'^(.+?[.!?])\s', text)
    if match and len(match.group(1)) <= max_length:
        return match.group(1)
    
    # Truncate
    return text[:max_length].strip() + "..."
