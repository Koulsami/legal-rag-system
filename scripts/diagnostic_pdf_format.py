#!/usr/bin/env python3
"""
Enhanced diagnostic script to investigate empty text fields.
Checks if PDFs were actually extracted or if text is stored elsewhere.
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.database.models import init_db, Document

def main():
    load_dotenv()
    db = init_db(os.getenv('DATABASE_URL'))
    
    print('='*80)
    print('🔍 COMPREHENSIVE DATABASE DIAGNOSTIC')
    print('='*80)
    print()
    
    with db.get_session() as session:
        # Check document count
        total = session.query(Document).count()
        print(f'✓ Total documents in database: {total}')
        
        # Check by type and level
        statutes = session.query(Document).filter_by(doc_type='statute').all()
        cases = session.query(Document).filter_by(doc_type='case').all()
        
        print(f'✓ Statutes: {len(statutes)}')
        print(f'✓ Cases: {len(cases)}')
        print()
        
        # Examine first statute in detail
        if statutes:
            s = statutes[0]
            print('='*80)
            print('📖 FIRST STATUTE - ALL FIELDS:')
            print('='*80)
            print(f'id: {s.id}')
            print(f'doc_type: {s.doc_type}')
            print(f'title: {s.title}')
            print(f'level: {s.level}')
            print(f'url: {s.url}')
            print(f'hash: {s.hash[:20] if s.hash else None}...')
            print(f'parent_id: {s.parent_id}')
            print(f'full_text type: {type(s.full_text)}')
            print(f'full_text is None: {s.full_text is None}')
            print(f'full_text length: {len(s.full_text) if s.full_text else 0}')
            if s.full_text:
                print(f'full_text first 500 chars:')
                print('-'*80)
                print(repr(s.full_text[:500]))
                print('-'*80)
            else:
                print('⚠️ full_text is NULL or empty!')
            print()
        
        # Examine first case in detail
        if cases:
            c = cases[0]
            print('='*80)
            print('⚖️ FIRST CASE - ALL FIELDS:')
            print('='*80)
            print(f'id: {c.id}')
            print(f'doc_type: {c.doc_type}')
            print(f'title: {c.title}')
            print(f'level: {c.level}')
            print(f'url: {c.url}')
            print(f'hash: {c.hash[:20] if c.hash else None}...')
            print(f'parent_id: {c.parent_id}')
            print(f'full_text type: {type(c.full_text)}')
            print(f'full_text is None: {c.full_text is None}')
            print(f'full_text length: {len(c.full_text) if c.full_text else 0}')
            if c.full_text:
                print(f'full_text first 500 chars:')
                print('-'*80)
                print(repr(c.full_text[:500]))
                print('-'*80)
            else:
                print('⚠️ full_text is NULL or empty!')
            print()
        
        # Check for any documents with non-empty text
        docs_with_text = session.query(Document).filter(
            Document.full_text != None,
            Document.full_text != ''
        ).count()
        print(f'✓ Documents with non-empty text: {docs_with_text} / {total}')
        print()

if __name__ == '__main__':
    main()
