#!/usr/bin/env python3
"""
Diagnostic script to examine PDF text format after extraction.
This will help us understand what section/paragraph markers look like.
"""

import os
import sys
from dotenv import load_dotenv

# Add project root to path
sys.path.insert(0, '/home/amee/legal-rag-poc')

from src.database.models import init_db, Document

def main():
    load_dotenv()
    db = init_db(os.getenv('DATABASE_URL'))
    
    print("=" * 80)
    print("PDF TEXT FORMAT DIAGNOSTIC")
    print("=" * 80)
    print()
    
    with db.get_session() as session:
        # ========================================
        # CHECK STATUTE FORMAT
        # ========================================
        statute = session.query(Document).filter_by(
            doc_type='statute', 
            level=0
        ).first()
        
        if statute:
            print("📖 STATUTE TEXT SAMPLE")
            print("=" * 80)
            print(f"Title: {statute.title}")
            print(f"Act Name: {statute.act_name}")
            print(f"Total Length: {len(statute.full_text)} characters")
            print()
            print("First 2000 characters:")
            print("-" * 80)
            print(statute.full_text[:2000])
            print("-" * 80)
            print()
            
            # Check for common section patterns
            text_sample = statute.full_text[:5000]
            patterns_to_check = [
                ("Section X", "Section" in text_sample or "SECTION" in text_sample),
                ("Sec. X", "Sec." in text_sample),
                ("§X", "§" in text_sample),
                ("Article X", "Article" in text_sample or "ARTICLE" in text_sample),
                ("X.", any(f"\n{i}." in text_sample for i in range(1, 20))),
                ("(X)", any(f"({i})" in text_sample for i in range(1, 10))),
                ("[X]", any(f"[{i}]" in text_sample for i in range(1, 10))),
            ]
            
            print("PATTERN DETECTION:")
            print("-" * 80)
            for pattern_name, found in patterns_to_check:
                status = "✓ FOUND" if found else "✗ Not found"
                print(f"{pattern_name:20s} {status}")
            print()
        else:
            print("❌ No statute found in database!")
            print()
        
        # ========================================
        # CHECK CASE FORMAT
        # ========================================
        case = session.query(Document).filter_by(
            doc_type='case', 
            level=0
        ).first()
        
        if case:
            print("=" * 80)
            print("⚖️  CASE TEXT SAMPLE")
            print("=" * 80)
            print(f"Title: {case.title}")
            print(f"Citation: {case.citation}")
            print(f"Total Length: {len(case.full_text)} characters")
            print()
            print("First 2000 characters:")
            print("-" * 80)
            print(case.full_text[:2000])
            print("-" * 80)
            print()
            
            # Check for common paragraph patterns
            text_sample = case.full_text[:5000]
            para_patterns = [
                ("[X]", any(f"[{i}]" in text_sample for i in range(1, 20))),
                ("X.", any(f"\n{i}." in text_sample for i in range(1, 20))),
                ("¶X", "¶" in text_sample),
                ("Para X", "Para" in text_sample or "para" in text_sample),
                ("Paragraph X", "Paragraph" in text_sample or "paragraph" in text_sample),
            ]
            
            print("PARAGRAPH PATTERN DETECTION:")
            print("-" * 80)
            for pattern_name, found in para_patterns:
                status = "✓ FOUND" if found else "✗ Not found"
                print(f"{pattern_name:20s} {status}")
            print()
        else:
            print("❌ No case found in database!")
            print()
        
        # ========================================
        # SUMMARY
        # ========================================
        print("=" * 80)
        print("DATABASE SUMMARY")
        print("=" * 80)
        total = session.query(Document).count()
        statutes = session.query(Document).filter_by(doc_type='statute').count()
        cases = session.query(Document).filter_by(doc_type='case').count()
        sections = session.query(Document).filter(
            Document.doc_type == 'statute',
            Document.level > 0
        ).count()
        paragraphs = session.query(Document).filter(
            Document.doc_type == 'case',
            Document.level > 0
        ).count()
        
        print(f"Total documents: {total}")
        print(f"Statutes (root): {statutes}")
        print(f"Cases (root): {cases}")
        print(f"Statute sections/subsections: {sections} ❌ (should be 150+)")
        print(f"Case paragraphs: {paragraphs} ❌ (should be 1000+)")
        print()
        
        print("=" * 80)
        print("NEXT STEPS")
        print("=" * 80)
        print("1. Review the text samples above")
        print("2. Identify the actual section/paragraph markers used")
        print("3. Update parser regex patterns to match")
        print("4. Clear database and re-ingest")
        print("=" * 80)

if __name__ == "__main__":
    main()
