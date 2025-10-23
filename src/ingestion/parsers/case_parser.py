"""
Fixed Case Parser - Uses doc_type='case' for all levels
Level field distinguishes: 0=Judgment, 1=Paragraph
"""
import re
from typing import List, Optional, Tuple
from datetime import datetime
import hashlib

from ..models import SourceDocument, ParsedDocument
from ..interfaces import DocumentParser


class CaseParser(DocumentParser):
    """Parse Singapore case PDFs into hierarchical structure"""
    
    def __init__(self, config: dict = None):
        """Initialize parser with optional config"""
        self.config = config or {}
        
        # Matches "1          " (number + 2+ spaces + capital letter)
        self.para_pattern = re.compile(
            r'^\s*(\d+)\s{2,}([A-Z].+?)(?=^\s*\d+\s{2,}[A-Z]|$)',
            re.MULTILINE | re.DOTALL
        )
        
        # Citation pattern: [2004] SGHC 32
        self.citation_pattern = re.compile(
            r'\[(\d{4})\]\s+([A-Z]+(?:\([A-Z]+\))?)\s+(\d+)'
        )
    
    def supports_format(self, source_doc: SourceDocument) -> bool:
        """Check if this parser can handle the document"""
        if source_doc.metadata and source_doc.metadata.get('doc_type') == 'case':
            return True
        
        text = source_doc.raw_content[:2000]
        if self.citation_pattern.search(text):
            return True
        
        if self.citation_pattern.search(source_doc.filepath):
            return True
        
        return False
    
    def parse(self, source_doc: SourceDocument) -> List[ParsedDocument]:
        """Parse case into hierarchy"""
        results = []
        text = source_doc.raw_content
        filepath = source_doc.filepath
        
        citation = self._extract_citation(filepath, text)
        parties = self._extract_parties(filepath, text)
        court, year = self._extract_court_year(citation)
        case_id = self._generate_case_id(citation)
        
        # 1. Root judgment (Level 0) - doc_type='case'
        root_doc = ParsedDocument(
            id=case_id,
            doc_type='case',  # ✅ Base type only
            parent_id=None,
            level=0,
            title=citation,
            full_text=text,
            citation=citation,
            court=court,
            year=year,
            parties=parties,
            jurisdiction='SG',
            url=None,
            hash=self._compute_hash(text),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        results.append(root_doc)
        
        # 2. Extract paragraphs (Level 1) - doc_type='case'
        paragraphs = self._extract_paragraphs(text, case_id, citation, court, year, parties)
        results.extend(paragraphs)
        
        return results
    
    def _extract_citation(self, filepath: str, text: str) -> str:
        """Extract case citation"""
        filename = filepath.split('/')[-1]
        match = self.citation_pattern.search(filename)
        if match:
            return match.group(0)
        
        lines = text.split('\n')[:10]
        for line in lines:
            match = self.citation_pattern.search(line)
            if match:
                return match.group(0)
        
        return filename.replace('.pdf', '')
    
    def _extract_parties(self, filepath: str, text: str) -> str:
        """Extract party names"""
        filename = filepath.split('/')[-1].replace('.pdf', '')
        parties = self.citation_pattern.sub('', filename).strip()
        
        if parties:
            return parties
        
        first_line = text.split('\n')[0].strip()
        parties = self.citation_pattern.sub('', first_line).strip()
        return parties if parties else filename
    
    def _extract_court_year(self, citation: str) -> Tuple[Optional[str], Optional[int]]:
        """Extract court and year from citation"""
        match = self.citation_pattern.search(citation)
        if match:
            year = int(match.group(1))
            court = match.group(2)
            return court, year
        return None, None
    
    def _generate_case_id(self, citation: str) -> str:
        """Generate ID from citation"""
        id_str = citation.lower()
        id_str = re.sub(r'[\[\]\s]', '_', id_str)
        id_str = re.sub(r'_+', '_', id_str)
        id_str = id_str.strip('_')
        return id_str
    
    def _extract_paragraphs(
        self,
        text: str,
        parent_id: str,
        citation: str,
        court: Optional[str],
        year: Optional[int],
        parties: str
    ) -> List[ParsedDocument]:
        """Extract Level 1 paragraphs"""
        paragraphs = []
        matches = list(self.para_pattern.finditer(text))
        
        if not matches:
            print(f"WARNING: No paragraphs found in {citation}")
            return []
        
        for i, match in enumerate(matches):
            para_no = int(match.group(1))
            para_text = match.group(2).strip()
            
            para_id = f"{parent_id}_para_{para_no}"
            
            if i + 1 < len(matches):
                full_text = text[match.start():matches[i + 1].start()].strip()
            else:
                full_text = text[match.start():].strip()
            
            title = f"¶{para_no}: {para_text[:100]}"
            
            para_doc = ParsedDocument(
                id=para_id,
                doc_type='case',  # ✅ Base type only
                parent_id=parent_id,
                level=1,
                title=title,
                full_text=full_text,
                citation=citation,
                court=court,
                year=year,
                parties=parties,
                para_no=para_no,
                jurisdiction='SG',
                url=None,
                hash=self._compute_hash(full_text),
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            paragraphs.append(para_doc)
        
        return paragraphs
    
    def _compute_hash(self, text: str) -> str:
        """Compute SHA256 hash of text"""
        return hashlib.sha256(text.encode('utf-8')).hexdigest()
