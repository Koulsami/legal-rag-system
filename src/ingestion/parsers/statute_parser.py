"""
Fixed Statute Parser - Uses doc_type='statute' for all levels
Level field distinguishes: 0=Act, 1=Section, 2=Subsection
"""
import re
from typing import List, Optional
from datetime import datetime
import hashlib

from ..models import SourceDocument, ParsedDocument
from ..interfaces import DocumentParser


class StatuteParser(DocumentParser):
    """Parse Singapore statute PDFs into hierarchical structure"""
    
    def __init__(self, config: dict = None):
        """Initialize parser with optional config"""
        self.config = config or {}
        
        # Matches "1.", "2.", "3A." without "Section" keyword
        self.section_pattern = re.compile(
            r'^\s*(\d+[A-Z]?)\.\s*(.+?)(?=^\s*\d+[A-Z]?\.|$)',
            re.MULTILINE | re.DOTALL
        )
        
        # Matches "(1)", "(2)", "(a)", "(b)" and "2.—(1)" format
        self.subsection_pattern = re.compile(
            r'^\s*(?:\d+\.—)?\(([a-z0-9]+)\)\s+(.+?)(?=^\s*\(|^\s*\d+[A-Z]?\.|$)',
            re.MULTILINE | re.DOTALL
        )
    
    def supports_format(self, source_doc: SourceDocument) -> bool:
        """Check if this parser can handle the document"""
        if source_doc.metadata and source_doc.metadata.get('doc_type') == 'statute':
            return True
        
        text = source_doc.raw_content[:2000]
        if 'ACT' in text.upper() and ('Section' in text or re.search(r'^\s*\d+\.', text, re.MULTILINE)):
            return True
        
        return False
    
    def parse(self, source_doc: SourceDocument) -> List[ParsedDocument]:
        """Parse statute into hierarchy"""
        results = []
        text = source_doc.raw_content
        filepath = source_doc.filepath
        
        act_name = self._extract_act_name(filepath, text)
        act_id = self._generate_act_id(act_name)
        
        # 1. Root Act (Level 0) - doc_type='statute'
        root_doc = ParsedDocument(
            id=act_id,
            doc_type='statute',  # ✅ Base type only
            parent_id=None,
            level=0,
            title=act_name,
            full_text=text,
            act_name=act_name,
            jurisdiction='SG',
            url=None,
            hash=self._compute_hash(text),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        results.append(root_doc)
        
        # 2. Skip TOC
        text_body = self._skip_toc(text)
        
        # 3. Extract sections (Level 1) - doc_type='statute'
        sections = self._extract_sections(text_body, act_id, act_name)
        
        # 4. Deduplicate
        seen_ids = {root_doc.id}
        unique_sections = []
        for section in sections:
            if section.id not in seen_ids:
                unique_sections.append(section)
                seen_ids.add(section.id)
                results.append(section)
        
        # 5. Extract subsections (Level 2) - doc_type='statute'
        for section in unique_sections:
            subsections = self._extract_subsections(
                section.full_text,
                section.id,
                section.section_number,
                act_name
            )
            for subsection in subsections:
                if subsection.id not in seen_ids:
                    results.append(subsection)
                    seen_ids.add(subsection.id)
        
        return results
    
    def _extract_act_name(self, filepath: str, text: str) -> str:
        """Extract act name from filepath or text"""
        filename = filepath.split('/')[-1].replace('.pdf', '')
        filename = filename.replace('_', ' ').title()
        
        lines = text.split('\n')[:20]
        for line in lines:
            if 'ACT' in line.upper() and len(line) < 100:
                act_name = line.strip()
                act_name = re.sub(r'\d{4}\s+REVISED EDITION', '', act_name)
                act_name = act_name.strip()
                if act_name:
                    return act_name
        
        return filename
    
    def _generate_act_id(self, act_name: str) -> str:
        """Generate ID from act name"""
        id_str = act_name.lower()
        id_str = re.sub(r'[^\w\s]', '', id_str)
        id_str = re.sub(r'\s+', '_', id_str)
        return id_str
    
    def _skip_toc(self, text: str) -> str:
        """Skip table of contents by finding date marker"""
        date_pattern = re.compile(r'\[\d{1,2}\s+\w+\s+\d{4}\]')
        match = date_pattern.search(text)
        if match:
            return text[match.start():]
        return text
    
    def _extract_sections(
        self,
        text: str,
        parent_id: str,
        act_name: str
    ) -> List[ParsedDocument]:
        """Extract Level 1 sections"""
        sections = []
        matches = list(self.section_pattern.finditer(text))
        
        for i, match in enumerate(matches):
            section_num = match.group(1)
            section_text = match.group(2).strip()
            
            first_newline = section_text.find('\n')
            if first_newline > 0:
                title = section_text[:first_newline].strip()
            else:
                title = section_text[:100].strip()
            
            section_id = f"{parent_id}_s{section_num.lower()}"
            
            if i + 1 < len(matches):
                full_text = text[match.start():matches[i + 1].start()].strip()
            else:
                full_text = text[match.start():].strip()
            
            section_doc = ParsedDocument(
                id=section_id,
                doc_type='statute',  # ✅ Base type only
                parent_id=parent_id,
                level=1,
                title=title,
                full_text=full_text,
                section_number=section_num,
                act_name=act_name,
                jurisdiction='SG',
                url=None,
                hash=self._compute_hash(full_text),
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            sections.append(section_doc)
        
        return sections
    
    def _extract_subsections(
        self,
        section_text: str,
        parent_id: str,
        section_number: str,
        act_name: str
    ) -> List[ParsedDocument]:
        """Extract Level 2 subsections"""
        subsections = []
        matches = list(self.subsection_pattern.finditer(section_text))
        
        for i, match in enumerate(matches):
            subsection_id = match.group(1)
            subsection_text = match.group(2).strip()
            
            sub_id = f"{parent_id}_{subsection_id}"
            
            if i + 1 < len(matches):
                full_text = section_text[match.start():matches[i + 1].start()].strip()
            else:
                full_text = section_text[match.start():].strip()
            
            title = subsection_text[:100].strip()
            
            subsection_doc = ParsedDocument(
                id=sub_id,
                doc_type='statute',  # ✅ Base type only
                parent_id=parent_id,
                level=2,
                title=title,
                full_text=full_text,
                section_number=section_number,
                subsection=subsection_id,
                act_name=act_name,
                jurisdiction='SG',
                url=None,
                hash=self._compute_hash(full_text),
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            subsections.append(subsection_doc)
        
        return subsections
    
    def _compute_hash(self, text: str) -> str:
        """Compute SHA256 hash of text"""
        return hashlib.sha256(text.encode('utf-8')).hexdigest()
