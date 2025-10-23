#!/usr/bin/env python3
"""Final working ingestion"""
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
print("WEEK 3 DATABASE REBUILD - FINAL INGESTION")
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
    
    # source_type should match doc_type
    source = SourceDocument(
        filepath=str(pdf_file),
        raw_content=text,
        doc_type='statute',
        source_type='statute',  # Must match doc_type
        format='pdf'
    )
    
    parsed = statute_parser.parse(source)
    all_docs.extend(parsed)
    print(f"      ✓ Parsed: {len(parsed)} documents (levels: {set(d.level for d in parsed)})")

statute_count = len([d for d in all_docs if d.doc_type == 'statute'])
print(f"   Total statutes: {statute_count}")

# ============================================================================
# 2. CASES
# ============================================================================
print("\n[2/3] Processing Cases (first 10 for testing)...")

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
        source_type='case',  # Must match doc_type
        format='pdf'
    )
    
    parsed = case_parser.parse(source)
    all_docs.extend(parsed)
    print(f"      ✓ Parsed: {len(parsed)} documents (levels: {set(d.level for d in parsed)})")

case_count = len([d for d in all_docs if d.doc_type == 'case'])
print(f"   Total cases: {case_count}")

# ============================================================================
# 3. RULES OF COURT
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
        source_type='rule',  # Must match doc_type
        format='pdf'
    )
    
    rules_parser = RulesParser(ParserConfig(extract_facts=False))
    parsed = rules_parser.parse(source)
    all_docs.extend(parsed)
    print(f"      ✓ Parsed: {len(parsed)} documents")
    
    # Show breakdown
    levels = {}
    for d in parsed:
        levels[d.level] = levels.get(d.level, 0) + 1
    print(f"      Levels: {levels}")
else:
    print(f"   ✗ Not found: {rules_pdf}")

rules_count = len([d for d in all_docs if d.doc_type == 'rule'])
print(f"   Total rules: {rules_count}")

# ============================================================================
# 4. INSERT TO DATABASE
# ============================================================================
print(f"\n[4/5] Inserting {len(all_docs)} documents to database...")

# Sort by level (0, 1, 2, 3) to avoid FK violations
all_docs_sorted = sorted(all_docs, key=lambda d: d.level)

inserted = 0
errors = 0
error_details = []

with db.get_session() as session:
    for i, doc in enumerate(all_docs_sorted):
        try:
            db_doc = Document(
                id=doc.id,
                doc_type=doc.doc_type,
                parent_id=doc.parent_id,
                level=doc.level,
                title=doc.title,
                full_text=doc.full_text,
                citation=doc.citation,
                court=doc.court,
                year=doc.year,
                parties=doc.parties,
                para_no=doc.para_no,
                section_number=doc.section_number,
                subsection=doc.subsection,
                section_title=doc.section_title,
                act_name=doc.act_name,
                jurisdiction=doc.jurisdiction,
                url=doc.url,
                hash=doc.hash,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            session.add(db_doc)
            inserted += 1
            
            if (i + 1) % 50 == 0:
                session.commit()
                print(f"   ✓ Batch committed: {inserted} documents")
        
        except Exception as e:
            errors += 1
            if errors <= 3:
                error_details.append(f"{doc.id}: {str(e)[:80]}")
    
    session.commit()

print(f"\n   Inserted: {inserted}")
print(f"   Errors: {errors}")
if error_details:
    print("   First errors:")
    for err in error_details:
        print(f"      - {err}")

# ============================================================================
# 5. VERIFICATION
# ============================================================================
print("\n[5/5] Verifying...")

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
    
    # Critical checks
    sections = session.query(Document).filter(
        Document.doc_type == 'statute',
        Document.level == 1
    ).count()
    
    subsections = session.query(Document).filter(
        Document.doc_type == 'statute',
        Document.level == 2
    ).count()
    
    paragraphs = session.query(Document).filter(
        Document.doc_type == 'case',
        Document.level == 1
    ).count()
    
    orphans = session.query(Document).filter(
        Document.parent_id.isnot(None),
        ~Document.parent_id.in_(session.query(Document.id))
    ).count()

print("\n" + "=" * 70)
print("RESULTS")
print("=" * 70)
print(f"\nTotal Documents: {total}")
print("\nBy Type:")
for doc_type, count in by_type:
    print(f"  {doc_type}: {count}")

print("\nBy Level:")
for level, count in by_level:
    label = {0: "roots", 1: "sections/orders/paragraphs", 2: "subsections/rules", 3: "sub-rules"}
    print(f"  Level {level} ({label.get(level, 'unknown')}): {count}")

print("\nCritical Metrics:")
print(f"  ✓ Statute sections (Level 1): {sections}")
print(f"  ✓ Statute subsections (Level 2): {subsections}")
print(f"  ✓ Case paragraphs (Level 1): {paragraphs}")
print(f"  {'✓' if orphans == 0 else '✗'} Orphaned documents: {orphans}")

print("\n" + "=" * 70)
if sections > 0 and paragraphs > 0 and orphans == 0:
    print("✓✓✓ SUCCESS! Database ready for Week 4!")
else:
    print("⚠ Warning: Check metrics above")
print("=" * 70 + "\n")
