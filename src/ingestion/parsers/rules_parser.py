"""
Rules of Court Parser - RELAXED Pattern
Catches rules even if they don't start with (1)
"""

from typing import List, Dict
import re
from ..models import ParsedDocument, SourceDocument, ParserConfig
import hashlib


class RulesParser:
    """Parser for Singapore Rules of Court documents"""
    
    def __init__(self, config: ParserConfig):
        self.config = config
    
    def parse(self, source: SourceDocument) -> List[ParsedDocument]:
        """Parse Rules of Court into 3-level hierarchy"""
        
        text = source.raw_content
        documents = []
        
        print("\n🔍 Skipping TOC...")
        
        # Skip Table of Contents
        page_marker = re.search(r'\n34\n', text)
        if page_marker:
            text = text[page_marker.end():]
            print(f"✅ Skipped first {page_marker.end():,} characters (TOC)")
        
        # Root Document
        root_doc = ParsedDocument(
            id="rules_of_court_2021",
            doc_type="rule",
            parent_id=None,
            level=0,
            title="Rules of Court 2021",
            full_text=text[:500],
            jurisdiction="Singapore",
            hash=hashlib.sha256(text.encode()).hexdigest()
        )
        documents.append(root_doc)
        
        # ============================================================
        # Find all Rule headers - RELAXED PATTERN
        # ============================================================
        
        # Pattern 1: Standard - (O. X, r. Y) followed by Y.—(1) or Y.—(2) etc
        pattern1 = r'([^\n]+)\s*\(O\.\s*(\d+),\s*r\.\s*(\d+)\)\s*\n+\s*\3\.—\([0-9]+\)'
        
        # Pattern 2: Relaxed - (O. X, r. Y) followed by just Y.— (no sub-rule number)
        pattern2 = r'([^\n]+)\s*\(O\.\s*(\d+),\s*r\.\s*(\d+)\)\s*\n+\s*\3\.—'
        
        # Try pattern 1 first (strictest)
        rule_matches_1 = list(re.finditer(pattern1, text))
        print(f"✅ Pattern 1 (strict): Found {len(rule_matches_1)} rules")
        
        # Try pattern 2 (relaxed)
        rule_matches_2 = list(re.finditer(pattern2, text))
        print(f"✅ Pattern 2 (relaxed): Found {len(rule_matches_2)} rules")
        
        # Use pattern 1 if it found reasonable number, else use pattern 2
        if len(rule_matches_1) >= 500:
            rule_matches = rule_matches_1
            print("→ Using Pattern 1 results")
        else:
            rule_matches = rule_matches_2
            print("→ Using Pattern 2 results")
        
        # ============================================================
        # Extract Order titles
        # ============================================================
        
        order_title_pattern = r'\nORDER\s+(\d+)\s*\n([A-Z][^\n]+)'
        order_title_matches = {
            match.group(1): match.group(2).strip()
            for match in re.finditer(order_title_pattern, text)
        }
        
        print(f"✅ Found {len(order_title_matches)} Order titles")
        
        # Group rules by Order
        rules_by_order: Dict[str, list] = {}
        
        for i, match in enumerate(rule_matches):
            rule_label = match.group(1).strip()
            order_num = match.group(2)
            rule_num = match.group(3)
            
            # Clean up label
            rule_label = re.sub(r'^\d+\.\s*', '', rule_label)
            rule_label = rule_label.strip()
            
            # Find rule content
            content_start = match.end() - len(f"{rule_num}.—")
            
            if i + 1 < len(rule_matches):
                content_end = rule_matches[i + 1].start()
            else:
                content_end = len(text)
            
            rule_content = text[content_start:content_end].strip()
            
            # Store rule info
            if order_num not in rules_by_order:
                rules_by_order[order_num] = []
            
            rules_by_order[order_num].append({
                'rule_num': rule_num,
                'label': rule_label,
                'content': rule_content
            })
        
        # ============================================================
        # Create Order and Rule documents
        # ============================================================
        
        for order_num in sorted(rules_by_order.keys(), key=int):
            order_title = order_title_matches.get(order_num, f"Order {order_num}")
            
            # Create Order document (Level 1)
            order_id = f"roc_2021_o_{order_num}"
            
            order_full_text = f"ORDER {order_num}\n{order_title}\n\n"
            for rule in rules_by_order[order_num]:
                order_full_text += f"Rule {rule['rule_num']}: {rule['label']}\n"
            
            order_doc = ParsedDocument(
                id=order_id,
                doc_type="rule",
                parent_id="rules_of_court_2021",
                level=1,
                title=f"Order {order_num}: {order_title}",
                full_text=order_full_text,
                section_number=order_num,
                section_title=order_title,
                jurisdiction="Singapore",
                hash=hashlib.sha256(order_full_text.encode()).hexdigest()
            )
            
            documents.append(order_doc)
            
            # Create Rule documents (Level 2)
            for rule in rules_by_order[order_num]:
                rule_id = f"{order_id}_r_{rule['rule_num']}"
                
                rule_doc = ParsedDocument(
                    id=rule_id,
                    doc_type="rule",
                    parent_id=order_id,
                    level=2,
                    title=f"Rule {rule['rule_num']}: {rule['label']}",
                    full_text=rule['content'],
                    section_number=rule['rule_num'],
                    section_title=rule['label'],
                    act_name=f"Order {order_num}",
                    jurisdiction="Singapore",
                    hash=hashlib.sha256(rule['content'].encode()).hexdigest()
                )
                
                documents.append(rule_doc)
        
        orders_count = len(rules_by_order)
        rules_count = sum(len(rules) for rules in rules_by_order.values())
        
        print(f"✅ Created {orders_count} Orders (Level 1)")
        print(f"✅ Created {rules_count} Rules (Level 2)")
        print(f"Total parsed: {len(documents)}")
        
        return documents
