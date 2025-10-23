#!/usr/bin/env python3
"""
Verify Rules of Court - Order 2, Rule 1
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import os
from dotenv import load_dotenv
from src.database.models import init_db, Document

load_dotenv()

# Initialize database
db = init_db(os.getenv('DATABASE_URL'))

with db.get_session() as session:
    print('='*80)
    print('RULES OF COURT VERIFICATION - ORDER 2, RULE 1')
    print('='*80)
    
    # 1. Check if Order 2 exists
    order_2_id = 'rules_of_court_2021_order_2'
    order_2 = session.query(Document).filter_by(id=order_2_id).first()
    
    if not order_2:
        print(f'\n❌ ORDER 2 NOT FOUND!')
        print(f'   Expected ID: {order_2_id}')
        
        # Show what Orders we do have
        print('\n📜 Available Orders:')
        orders = session.query(Document).filter_by(
            doc_type='rule',
            level=1
        ).order_by(Document.section_number).limit(10).all()
        
        for order in orders:
            print(f'   - {order.id} (Section: {order.section_number})')
        
        sys.exit(1)
    
    print(f'\n✅ ORDER 2 FOUND')
    print(f'   ID: {order_2.id}')
    print(f'   Section Number: {order_2.section_number}')
    print(f'   Title: {order_2.title}')
    print(f'   Level: {order_2.level}')
    print(f'   Text Length: {len(order_2.full_text)} characters')
    
    # 2. Check if Rule 1 of Order 2 exists
    rule_1_id = 'rules_of_court_2021_order_2_r1'
    rule_1 = session.query(Document).filter_by(id=rule_1_id).first()
    
    if not rule_1:
        print(f'\n❌ RULE 1 OF ORDER 2 NOT FOUND!')
        print(f'   Expected ID: {rule_1_id}')
        
        # Show what Rules we have in Order 2
        print(f'\n📜 Available Rules in Order 2:')
        rules = session.query(Document).filter_by(
            parent_id=order_2_id,
            level=2
        ).all()
        
        if rules:
            for rule in rules[:10]:
                print(f'   - {rule.id} (Section: {rule.section_number})')
        else:
            print('   No rules found in Order 2')
        
        sys.exit(1)
    
    print(f'\n✅ RULE 1 OF ORDER 2 FOUND')
    print(f'   ID: {rule_1.id}')
    print(f'   Section Number: {rule_1.section_number}')
    print(f'   Title: {rule_1.title}')
    print(f'   Level: {rule_1.level}')
    print(f'   Parent ID: {rule_1.parent_id}')
    print(f'   Text Length: {len(rule_1.full_text)} characters')
    
    # 3. Display the full text
    print('\n' + '='*80)
    print('FULL TEXT OF ORDER 2, RULE 1')
    print('='*80)
    print(rule_1.full_text)
    print('='*80)
    
    # 4. Check all rules in Order 2
    all_rules = session.query(Document).filter_by(
        parent_id=order_2_id,
        level=2
    ).order_by(Document.section_number).all()
    
    print(f'\n📜 ALL RULES IN ORDER 2 (Total: {len(all_rules)})')
    print('='*80)
    for rule in all_rules:
        print(f'   {rule.section_number}: {rule.title[:60]}...')
    print('='*80)

print('\n✅ Verification complete!')
