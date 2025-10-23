#!/usr/bin/env python3
"""Direct ingestion with correct SourceDocument"""
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
print("DIRECT INGESTION")
print("=" * 70)

# Initialize
db = init_db(os.getenv('DATABASE_URL', 'postgresql://localhost/legal_rag_dev'))

print("\n1. Processing Statutes...")

statute_parser = StatuteParser(ParserConfig(extract_facts=False))
statute_dir = Path('/home/amee/LegalDB/Statue')

all_docs = []

# Process statute PDFs
for pdf_file in statute_dir.glob('*.pdf'):
    if 'Rules' in pdf_file.name:
        continue
    
    print(f"   Processing: {pdf_file.name}")
    
    with open(pdf_file, 'rb') as f:
        reader = PyPDF2.PdfReader(f)
        text = ''.join(page.extract_text() for page in reader.pages)
    
    # Create SourceDocument with required fields
    source = SourceDocument(
        filepath=str(pdf_file),
        raw_content=text,
        doc_type='statute',
        source_type='filesystem',  # Required
        format='pdf'              # Required
    )
    
    parsed = statute_parser.parse(source)
    all_docs.extend(parsed)
    print(f"      Parsed: {len(parsed)} documents")

print(f"   Total: {len(all_docs)} statute documents")

print("\n2. Processing Cases (first 10)...")

case_parser = CaseParser(ParserConfig(extract_facts=False))
case_dir = Path('/home/amee/LegalDB/Case')

case_files = list(case_dir.glob('*.pdf'))[:10]
print(f"   Found {len(case_files)} case files")

for pdf_file in case_files:
    print(f"   Processing: {pdf_file.name}")
    
    with open(pdf_file, 'rb') as f:
        reader = PyPDF2.PdfReader(f)
        text = ''.join(page.extract_text() for page in reader.pages)
    
    source = SourceDocument(
        filepath=str(pdf_file),
        raw_content=text,
        doc_type='case',
        source_type='filesystem',
        format='pdf'
    )
    
    parsed = case_parser.parse(source)
    all_docs.extend(parsed)
    print(f"      Parsed: {len(parsed)} documents")

print(f"   Total: {len([d for d in all_docs if d.doc_type == 'case'])} case documents")

print("\n3. Processing Rules of Court...")

rules_pdf = Path('/home/amee/LegalDB/Statue/Rules_of_Court_2021.pdf.pdf')

if rules_pdf.exists():
    print(f"   Processing: {rules_pdf.name}")
    
    with open(rules_pdf, 'rb') as f:
        reader = PyPDF2.PdfReader(f)
        text = ''.join(page.extract_text() for page in reader.pages)
    
    source = SourceDocument(
        filepath=str(rules_pdf),
        raw_content=text,
        doc_type='rule',
        source_type='filesystem',
        format='pdf'
    )
    
    rules_parser = RulesParser(ParserConfig(extract_facts=False))
    parsed = rules_parser.parse(source)
    all_docs.extend(parsed)
    print(f"      Parsed: {len(parsed)} documents")

print(f"\n   TOTAL PARSED: {len(all_docs)} documents")

print("\n4. Inserting to database...")

# Sort by level to avoid FK violations
all_docs_sorted = sorted(all_docs, key=lambda d: d.level)

inserted = 0
skipped = 0
errors = 0

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
            
            # Commit every 50 docs
            if (i + 1) % 50 == 0:
                session.commit()
                print(f"      Committed batch: {inserted} docs so far")
        
        except Exception as e:
            errors += 1
            if errors <= 5:
                print(f"      Error on {doc.id}: {str(e)[:100]}")
    
    # Final commit
    session.commit()

print(f"\n   Inserted: {inserted}")
print(f"   Errors: {errors}")

print("\n5. Verification...")

with db.get_session() as session:
    from sqlalchemy import func
    
    total = session.query(Document).count()
    print(f"\n   Total documents: {total}")
    
    by_type = session.query(
        Document.doc_type,
        func.count(Document.id)
    ).group_by(Document.doc_type).all()
    
    print("\n   By type:")
    for doc_type, count in by_type:
        print(f"      {doc_type}: {count}")
    
    by_level = session.query(
        Document.level,
        func.count(Document.id)
    ).group_by(Document.level).order_by(Document.level).all()
    
    print("\n   By level:")
    for level, count in by_level:
        print(f"      Level {level}: {count}")
    
    # Check for sections and paragraphs
    sections = session.query(Document).filter(
        Document.doc_type == 'statute',
        Document.level == 1
    ).count()
    
    paragraphs = session.query(Document).filter(
        Document.doc_type == 'case',
        Document.level == 1
    ).count()
    
    print(f"\n   Statute sections (Level 1): {sections}")
    print(f"   Case paragraphs (Level 1): {paragraphs}")

print("\n" + "=" * 70)
print("INGESTION COMPLETE!")
print("=" * 70)
