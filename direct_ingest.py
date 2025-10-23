#!/usr/bin/env python3
"""Direct ingestion bypassing pipeline"""
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
print("DIRECT INGESTION (bypassing pipeline)")
print("=" * 70)

# Initialize
db = init_db(os.getenv('DATABASE_URL', 'postgresql://localhost/legal_rag_dev'))

print("\n1. Processing Statutes...")

statute_parser = StatuteParser(ParserConfig(extract_facts=False))
statute_dir = Path('/home/amee/LegalDB/Statue')

all_docs = []

# Process each statute PDF
for pdf_file in statute_dir.glob('*.pdf'):
    if 'Rules' in pdf_file.name:
        continue  # Skip Rules for now
    
    print(f"   Processing: {pdf_file.name}")
    
    # Extract text
    with open(pdf_file, 'rb') as f:
        reader = PyPDF2.PdfReader(f)
        text = ''.join(page.extract_text() for page in reader.pages)
    
    # Parse
    source = SourceDocument(filepath=str(pdf_file), raw_content=text, doc_type='statute')
    parsed = statute_parser.parse(source)
    all_docs.extend(parsed)
    print(f"      Parsed: {len(parsed)} documents")

print(f"   Total statute documents: {len(all_docs)}")

print("\n2. Processing Cases...")

case_parser = CaseParser(ParserConfig(extract_facts=False))
case_dir = Path('/home/amee/LegalDB/Case')

case_count = 0
for pdf_file in list(case_dir.glob('*.pdf'))[:10]:  # First 10 for testing
    print(f"   Processing: {pdf_file.name}")
    
    # Extract text
    with open(pdf_file, 'rb') as f:
        reader = PyPDF2.PdfReader(f)
        text = ''.join(page.extract_text() for page in reader.pages)
    
    # Parse
    source = SourceDocument(filepath=str(pdf_file), raw_content=text, doc_type='case')
    parsed = case_parser.parse(source)
    all_docs.extend(parsed)
    case_count += len(parsed)
    print(f"      Parsed: {len(parsed)} documents")

print(f"   Total case documents: {case_count}")

print("\n3. Processing Rules of Court...")

rules_pdf = Path('/home/amee/LegalDB/Statue/Rules_of_Court_2021.pdf.pdf')

if rules_pdf.exists():
    print(f"   Processing: {rules_pdf.name}")
    
    # Extract text
    with open(rules_pdf, 'rb') as f:
        reader = PyPDF2.PdfReader(f)
        text = ''.join(page.extract_text() for page in reader.pages)
    
    # Parse
    source = SourceDocument(filepath=str(rules_pdf), raw_content=text, doc_type='rule')
    rules_parser = RulesParser(ParserConfig(extract_facts=False))
    parsed = rules_parser.parse(source)
    all_docs.extend(parsed)
    print(f"      Parsed: {len(parsed)} documents")

print(f"\n4. Loading to database...")
print(f"   Total documents to insert: {len(all_docs)}")

# Sort by level
all_docs_sorted = sorted(all_docs, key=lambda d: d.level)

# Insert in batches
batch_size = 50
inserted = 0
errors = 0

with db.get_session() as session:
    for i in range(0, len(all_docs_sorted), batch_size):
        batch = all_docs_sorted[i:i + batch_size]
        
        for doc in batch:
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
            except Exception as e:
                errors += 1
                if errors <= 3:  # Show first 3 errors
                    print(f"      Error on {doc.id}: {e}")
        
        session.commit()
        print(f"      Batch {i//batch_size + 1}: {len(batch)} documents")

print(f"\n   Inserted: {inserted}")
print(f"   Errors: {errors}")

print("\n5. Verifying...")

with db.get_session() as session:
    from sqlalchemy import func
    
    total = session.query(Document).count()
    print(f"\n   Total: {total}")
    
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

print("\n" + "=" * 70)
print("DONE!")
print("=" * 70)
