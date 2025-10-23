#!/usr/bin/env python3
"""Fixed ingestion - handles attribute mismatches"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))

import os
from dotenv import load_dotenv
from src.database.models import init_db, Document
from src.ingestion.parsers.statute_parser import StatuteParser
from src.ingestion.parsers.case_parser import CaseParser
from src.ingestion.parsers.rules_parser import RulesParser
from src.ingestion.models import ParserConfig, SourceDocument
import PyPDF2
from datetime import datetime

load_dotenv()

print("=" * 70)
print("FIXED INGESTION - WEEK 3")
print("=" * 70)

db = init_db(os.getenv('DATABASE_URL', 'postgresql://localhost/legal_rag_dev'))

all_docs = []

# ============================================================================
# 1. STATUTES
# ============================================================================
print("\n[1/3] Processing Statutes...")

statute_parser = StatuteParser(ParserConfig(extract_facts=False))
statute_dir = Path('/home/amee/LegalDB/Statue')

for pdf_file in statute_dir.glob('*.pdf'):
    if 'Rules' in pdf_file.name:
        continue
    
    print(f"   📖 {pdf_file.name}")
    
    with open(pdf_file, 'rb') as f:
        reader = PyPDF2.PdfReader(f)
        text = ''.join(page.extract_text() for page in reader.pages)
    
    source = SourceDocument(
        filepath=str(pdf_file),
        raw_content=text,
        doc_type='statute',
        source_type='statute',
        format='pdf'
    )
    
    parsed = statute_parser.parse(source)
    all_docs.extend(parsed)
    print(f"      ✓ {len(parsed)} documents")

print(f"   Total: {len([d for d in all_docs if d.doc_type == 'statute'])} statutes")

# ============================================================================
# 2. CASES (first 10)
# ============================================================================
print("\n[2/3] Processing Cases...")

case_parser = CaseParser(ParserConfig(extract_facts=False))
case_dir = Path('/home/amee/LegalDB/Case')

case_files = sorted(case_dir.glob('*.pdf'))[:10]

for pdf_file in case_files:
    print(f"   ⚖️  {pdf_file.name}")
    
    with open(pdf_file, 'rb') as f:
        reader = PyPDF2.PdfReader(f)
        text = ''.join(page.extract_text() for page in reader.pages)
    
    source = SourceDocument(
        filepath=str(pdf_file),
        raw_content=text,
        doc_type='case',
        source_type='case',
        format='pdf'
    )
    
    parsed = case_parser.parse(source)
    all_docs.extend(parsed)
    print(f"      ✓ {len(parsed)} documents")

print(f"   Total: {len([d for d in all_docs if d.doc_type == 'case'])} cases")

# ============================================================================
# 3. RULES
# ============================================================================
print("\n[3/3] Processing Rules of Court...")

rules_pdf = Path('/home/amee/LegalDB/Statue/Rules_of_Court_2021.pdf.pdf')

if rules_pdf.exists():
    print(f"   📜 {rules_pdf.name}")
    
    with open(rules_pdf, 'rb') as f:
        reader = PyPDF2.PdfReader(f)
        text = ''.join(page.extract_text() for page in reader.pages)
    
    source = SourceDocument(
        filepath=str(rules_pdf),
        raw_content=text,
        doc_type='rule',
        source_type='rule',
        format='pdf'
    )
    
    rules_parser = RulesParser(ParserConfig(extract_facts=False))
    parsed = rules_parser.parse(source)
    all_docs.extend(parsed)
    print(f"      ✓ {len(parsed)} documents")

print(f"   Total: {len([d for d in all_docs if d.doc_type == 'rule'])} rules")

# ============================================================================
# 4. INSERT - WITH ATTRIBUTE SAFETY
# ============================================================================
print(f"\n[4/5] Inserting {len(all_docs)} documents...")

all_docs_sorted = sorted(all_docs, key=lambda d: d.level)

inserted = 0
errors = 0
error_details = []

with db.get_session() as session:
    for i, doc in enumerate(all_docs_sorted):
        try:
            # Use getattr() with defaults for optional fields
            db_doc = Document(
                id=doc.id,
                doc_type=doc.doc_type,
                parent_id=doc.parent_id,
                level=doc.level,
                title=doc.title,
                full_text=doc.full_text,
                
                # Optional fields - use getattr with None default
                citation=getattr(doc, 'citation', None),
                court=getattr(doc, 'court', None),
                year=getattr(doc, 'year', None),
                parties=getattr(doc, 'parties', None),
                para_no=getattr(doc, 'para_no', None),
                
                section_number=getattr(doc, 'section_number', None),
                subsection=getattr(doc, 'subsection', None),
                section_title=getattr(doc, 'section_title', None),
                act_name=getattr(doc, 'act_name', None),
                
                jurisdiction=getattr(doc, 'jurisdiction', None),
                url=getattr(doc, 'url', None),
                hash=doc.hash,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            session.add(db_doc)
            inserted += 1
            
            if (i + 1) % 100 == 0:
                session.commit()
                print(f"   ✓ {inserted} documents committed")
        
        except Exception as e:
            errors += 1
            if errors <= 5:
                error_details.append(f"{doc.id}: {str(e)[:100]}")
    
    session.commit()

print(f"\n   Inserted: {inserted}")
print(f"   Errors: {errors}")

if error_details:
    print("\n   Error details:")
    for err in error_details:
        print(f"      {err}")

# ============================================================================
# 5. VERIFICATION
# ============================================================================
print("\n[5/5] Verifying...")

try:
    with db.get_session() as session:
        from sqlalchemy import func
        
        total = session.query(Document).count()
        
        by_type = session.query(
            Document.doc_type,
            func.count(Document.id)
        ).group_by(Document.doc_type).all()
        
        by_level = session.query(
            Document.level,
            func.count(Document.id)
        ).group_by(Document.level).order_by(Document.level).all()
        
        orphans = session.query(Document).filter(
            Document.parent_id.isnot(None),
            ~Document.parent_id.in_(session.query(Document.id))
        ).count()
    
    print("\n" + "=" * 70)
    print("RESULTS")
    print("=" * 70)
    print(f"\nTotal: {total}")
    print("\nBy Type:")
    for doc_type, count in by_type:
        print(f"  {doc_type}: {count}")
    
    print("\nBy Level:")
    for level, count in by_level:
        print(f"  Level {level}: {count}")
    
    print(f"\nOrphans: {orphans}")
    
    if inserted > 0 and orphans == 0:
        print("\n✓ Ingestion successful!")
    else:
        print("\n⚠ Check results above")
    
    print("=" * 70 + "\n")

except Exception as e:
    print(f"\n✗ Verification error: {e}")
    print("\nBut ingestion may have succeeded - check manually:")
    print("  psql legal_rag_dev -c 'SELECT doc_type, COUNT(*) FROM documents GROUP BY doc_type;'")
