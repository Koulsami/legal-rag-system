"""
Fixed Rules Parser for Singapore Rules of Court 2021.
Correctly parses: Orders > Rules > Sub-rules
"""

import re
from typing import List
from datetime import datetime
import hashlib

from ..models import SourceDocument, ParsedDocument
from ..interfaces import DocumentParser


class RulesParser(DocumentParser):
    """Parser for Singapore Rules of Court 2021 PDF."""
    
    MIN_ORDER_LENGTH = 2000
    MIN_RULE_LENGTH = 50
    MIN_SUBRULE_LENGTH = 30
    
    def supports_format(self, source_doc: SourceDocument) -> bool:
        return (
            source_doc.metadata.get('doc_type') == 'rule' and
            'rules of court' in source_doc.filepath.lower()
        )
    
    def parse(self, source_doc: SourceDocument) -> List[ParsedDocument]:
        results = []
        
        # Skip TOC using page number detection
        text = self._skip_toc(source_doc.raw_content)
        
        if not text:
            print("⚠️  WARNING: Could not find start of actual content")
            text = source_doc.raw_content
        
        # Level 0: Create root document
        root_id = "rules_of_court_2021"
        root_doc = ParsedDocument(
            id=root_id,
            level=0,
            parent_id=None,
            doc_type='rule',
            title="Rules of Court 2021",
            full_text=text[:10000],
            jurisdiction='SG',
            url=None,
            hash=self._compute_hash(text[:10000]),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        results.append(root_doc)
        
        # Level 1: Extract Orders
        orders = self._extract_orders(text, root_id)
        print(f"✅ Extracted {len(orders)} Orders (Level 1)")
        
        # Level 2 & 3: Extract Rules and Sub-rules from each Order
        total_rules = 0
        total_subrules = 0
        
        for order in orders:
            results.append(order)
            
            # Extract Rules (Level 2)
            rules = self._extract_rules(order.full_text, order.id)
            total_rules += len(rules)
            
            for rule in rules:
                results.append(rule)
                
                # Extract Sub-rules (Level 3)
                subrules = self._extract_subrules(rule.full_text, rule.id)
                results.extend(subrules)
                total_subrules += len(subrules)
        
        print(f"✅ Extracted {total_rules} Rules (Level 2)")
        print(f"✅ Extracted {total_subrules} Sub-rules (Level 3)")
        
        return results
    
    def _skip_toc(self, text: str) -> str:
        """Skip TOC by finding page 34-40 markers."""
        print("🔍 Attempting to skip TOC using page number detection...")
        
        for page_num in range(34, 46):
            patterns = [
                f'S 914/2021 {page_num}',
                f'S 914/2021  {page_num}',
                f'S 914/2021{page_num}',
            ]
            
            for pattern in patterns:
                pos = text.find(pattern)
                if pos > 0:
                    result_text = text[pos + len(pattern):]
                    
                    print(f"✅ Found page {page_num} marker at position {pos}")
                    print(f"   Skipping first {pos:,} characters (TOC)")
                    
                    if len(result_text) > 50000:
                        return result_text
        
        print("⚠️  No page marker found, using ORDER length heuristic...")
        
        order_pattern = re.compile(r'ORDER\s+(\d+)', re.IGNORECASE)
        matches = list(order_pattern.finditer(text))
        
        for i, match in enumerate(matches):
            start_pos = match.start()
            
            if i + 1 < len(matches):
                section_len = matches[i+1].start() - start_pos
            else:
                section_len = len(text) - start_pos
            
            if section_len > 3000:
                print(f"✅ Found ORDER {match.group(1)} with {section_len:,} chars")
                return text[start_pos:]
        
        return text
    
    def _extract_orders(self, text: str, root_id: str) -> List[ParsedDocument]:
        """Extract Orders (Level 1)."""
        orders = []
        
        pattern = re.compile(
            r'ORDER\s+(\d+)\s*\n\s*(.*?)(?=ORDER\s+\d+|\Z)',
            re.DOTALL | re.IGNORECASE
        )
        
        matches = list(pattern.finditer(text))
        
        for match in matches:
            order_num = match.group(1)
            order_text = match.group(0).strip()
            
            # Extract title (first line after ORDER number)
            title_match = re.search(r'ORDER\s+\d+\s*\n\s*([A-Z][A-Z\s,]+?)\n', order_text)
            title = title_match.group(1).strip() if title_match else f"Order {order_num}"
            
            if len(order_text) < self.MIN_ORDER_LENGTH:
                continue
            
            order_id = f"{root_id}_order_{order_num}"
            
            order_doc = ParsedDocument(
                id=order_id,
                level=1,
                parent_id=root_id,
                doc_type='rule',
                title=f"Order {order_num}: {title}",
                section_number=order_num,
                section_title=title,
                full_text=order_text,
                jurisdiction='SG',
                url=None,
                hash=self._compute_hash(order_text),
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            orders.append(order_doc)
        
        return orders
    
    def _extract_rules(self, order_text: str, order_id: str) -> List[ParsedDocument]:
        """
        Extract Rules (Level 2) within an Order.
        
        Format:
            Title line: "Citation and commencement (O. 1, r. 1)"
            Rule text: "1. These Rules..." or "2.—(1) Subject to..."
        """
        rules = []
        
        # Pattern: Title line ending with (O. X, r. Y) followed by rule text
        pattern = re.compile(
            r'([^\n]+?)\s*\(O\.\s*\d+,\s*r\.\s*(\d+)\)\s*\n'
            r'((?:\2\.(?:—)?(?:\(\d+\))?.*?)(?=\n[A-Z].*?\(O\.\s*\d+,\s*r\.\s*\d+\)|\Z))',
            re.DOTALL
        )
        
        matches = list(pattern.finditer(order_text))
        
        for match in matches:
            title = match.group(1).strip()
            rule_num = match.group(2)
            rule_text = match.group(3).strip()
            
            if len(rule_text) < self.MIN_RULE_LENGTH:
                continue
            
            rule_id = f"{order_id}_r{rule_num}"
            
            # Create full text with title
            full_text = f"{title} (O. {order_id.split('_')[-1]}, r. {rule_num})\n{rule_text}"
            
            rule_doc = ParsedDocument(
                id=rule_id,
                level=2,
                parent_id=order_id,
                doc_type='rule',
                title=f"Rule {rule_num}: {title}",
                section_number=rule_num,
                section_title=title,
                full_text=full_text,
                jurisdiction='SG',
                url=None,
                hash=self._compute_hash(full_text),
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            rules.append(rule_doc)
        
        return rules
    
    def _extract_subrules(self, rule_text: str, rule_id: str) -> List[ParsedDocument]:
        """
        Extract Sub-rules (Level 3) within a Rule.
        
        Format: (1), (2), (3)... including nested (a), (b)...
        """
        subrules = []
        
        # Pattern: (number) followed by text until next (number) at start of line
        pattern = re.compile(
            r'(?:^|\n)\((\d+)\)\s+(.*?)(?=\n\(\d+\)|\Z)',
            re.DOTALL | re.MULTILINE
        )
        
        matches = list(pattern.finditer(rule_text))
        
        for match in matches:
            subrule_num = match.group(1)
            subrule_text = match.group(0).strip()
            
            if len(subrule_text) < self.MIN_SUBRULE_LENGTH:
                continue
            
            subrule_id = f"{rule_id}_{subrule_num}"
            
            # Title is first 60 chars
            title_text = subrule_text[:60].replace('\n', ' ').strip()
            if len(subrule_text) > 60:
                title_text += "..."
            
            subrule_doc = ParsedDocument(
                id=subrule_id,
                level=3,
                parent_id=rule_id,
                doc_type='rule',
                title=f"Sub-rule ({subrule_num}): {title_text}",
                subsection=subrule_num,
                full_text=subrule_text,
                jurisdiction='SG',
                url=None,
                hash=self._compute_hash(subrule_text),
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            subrules.append(subrule_doc)
        
        return subrules
    
    def _compute_hash(self, text: str) -> str:
        """Compute SHA256 hash"""
        return hashlib.sha256(text.encode('utf-8')).hexdigest()
