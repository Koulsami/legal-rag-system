#!/usr/bin/env python3
"""
Create a Sample Interpretation Link
Demonstrates the complete workflow for linking statutes to cases.
"""

from sqlalchemy import create_engine, text
import uuid
from datetime import datetime

DATABASE_URL = "postgresql://legal_rag:legal_rag_2025@localhost:5432/legal_rag_dev"

def get_document_details(engine, doc_id):
    """Fetch document details from database."""
    with engine.connect() as conn:
        result = conn.execute(
            text("""
                SELECT id, doc_type, title, full_text, citation, 
                       section_number, para_no, court, year
                FROM documents
                WHERE id = :doc_id
            """),
            {'doc_id': doc_id}
        )
        return result.fetchone()

def create_sample_link():
    """Create a sample interpretation link."""
    
    engine = create_engine(DATABASE_URL)
    
    print("="*60)
    print("CREATING SAMPLE INTERPRETATION LINK")
    print("="*60)
    print()
    
    # Example: Link Section 2(1) to a SGCA case
    statute_id = 'misrepresentation_act_1967_s2_1'
    case_id = '2000_sgca_28'  # Using first SGCA case
    
    # Fetch actual document data
    statute_doc = get_document_details(engine, statute_id)
    case_doc = get_document_details(engine, case_id)
    
    if not statute_doc:
        print(f"❌ Statute not found: {statute_id}")
        return
    
    if not case_doc:
        print(f"❌ Case not found: {case_id}")
        return
    
    print(f"📖 Statute: {statute_id}")
    print(f"   Section: {statute_doc.section_number}")
    print(f"   Text preview: {statute_doc.full_text[:100]}...")
    print()
    print(f"⚖️  Case: {case_id}")
    print(f"   Citation: {case_doc.citation}")
    print(f"   Court: {case_doc.court}")
    print(f"   Year: {case_doc.year}")
    print()
    
    # Create interpretation link
    link = {
        'id': str(uuid.uuid4()),
        'statute_id': statute_id,
        'case_id': case_id,
        
        # Statute details
        'statute_name': 'Misrepresentation Act 1967',
        'statute_section': '2(1)',
        'statute_text': statute_doc.full_text[:500] if statute_doc.full_text else '',
        
        # Case details
        'case_name': f'Case {case_doc.citation}',  # You can update this manually
        'case_citation': case_doc.citation or '[2000] SGCA 28',
        'case_para_no': case_doc.para_no or 1,  # Default to 1 if not parsed
        'case_text': case_doc.full_text[:500] if case_doc.full_text else '',
        'court': case_doc.court or 'SGCA',
        'year': case_doc.year or 2000,
        
        # Interpretation metadata
        'interpretation_type': 'CLARIFY',  # How this case interprets the statute
        'authority': 'BINDING',  # SGCA decisions are binding
        'holding': 'Court of Appeal clarified the application of Section 2(1) to pre-contractual misrepresentations',
        
        # Fact-pattern awareness
        'fact_pattern_tags': ['misrepresentation', 'damages', 'pre_contractual'],
        'case_facts_summary': 'Case involving damages claim for misrepresentation made during contract negotiations',
        'applicability_score': 0.8,  # Broadly applicable
        'cause_of_action': 'Misrepresentation',
        'sub_issues': ['damages', 'liability', 'pre_contractual_statements'],
        
        # Extraction metadata
        'extraction_method': 'MANUAL',
        'confidence': 1.0,
        
        # Verification
        'verified': True,
        'verified_by': 'legal_expert',
        'verified_at': datetime.now(),
        
        # Retrieval boost
        'boost_factor': 2.8  # High boost for SGCA binding decision
    }
    
    with engine.connect() as conn:
        trans = conn.begin()
        try:
            # Check if link already exists
            result = conn.execute(
                text("SELECT id FROM interpretation_links WHERE statute_id = :sid AND case_id = :cid"),
                {'sid': statute_id, 'cid': case_id}
            )
            
            if result.fetchone():
                print("⚠️  Link already exists between these documents")
                print("Skipping creation.")
                return
            
            # Insert link
            conn.execute(
                text("""
                    INSERT INTO interpretation_links (
                        id, statute_id, case_id,
                        statute_name, statute_section, statute_text,
                        case_name, case_citation, case_para_no, case_text,
                        court, year,
                        interpretation_type, authority, holding,
                        fact_pattern_tags, case_facts_summary, 
                        applicability_score, cause_of_action, sub_issues,
                        extraction_method, confidence,
                        verified, verified_by, verified_at,
                        boost_factor
                    ) VALUES (
                        :id, :statute_id, :case_id,
                        :statute_name, :statute_section, :statute_text,
                        :case_name, :case_citation, :case_para_no, :case_text,
                        :court, :year,
                        :interpretation_type, :authority, :holding,
                        :fact_pattern_tags, :case_facts_summary,
                        :applicability_score, :cause_of_action, :sub_issues,
                        :extraction_method, :confidence,
                        :verified, :verified_by, :verified_at,
                        :boost_factor
                    )
                """),
                link
            )
            
            trans.commit()
            
            print("✅ LINK CREATED SUCCESSFULLY!")
            print()
            print("Link Details:")
            print(f"  Statute: {link['statute_section']} - {link['statute_name']}")
            print(f"  Case: {link['case_citation']}")
            print(f"  Type: {link['interpretation_type']}")
            print(f"  Authority: {link['authority']}")
            print(f"  Boost Factor: {link['boost_factor']}x")
            print(f"  Cause of Action: {link['cause_of_action']}")
            print(f"  Fact Tags: {', '.join(link['fact_pattern_tags'])}")
            
        except Exception as e:
            trans.rollback()
            print(f"❌ Error creating link: {e}")
            raise
    
    engine.dispose()

def show_all_links():
    """Display all interpretation links."""
    
    engine = create_engine(DATABASE_URL)
    
    print("\n" + "="*60)
    print("ALL INTERPRETATION LINKS")
    print("="*60)
    
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT 
                statute_section,
                case_citation,
                interpretation_type,
                authority,
                boost_factor,
                verified,
                cause_of_action
            FROM interpretation_links
            ORDER BY statute_section, case_citation
        """))
        
        links = result.fetchall()
        
        if not links:
            print("\n⚠️  No links found")
        else:
            print(f"\nTotal links: {len(links)}\n")
            for link in links:
                status = "✅ Verified" if link.verified else "⚠️  Unverified"
                print(f"{status}")
                print(f"  Statute: {link.statute_section}")
                print(f"  Case: {link.case_citation}")
                print(f"  Type: {link.interpretation_type} | Authority: {link.authority}")
                print(f"  Boost: {link.boost_factor}x | Cause: {link.cause_of_action}")
                print()
    
    engine.dispose()

def test_retrieval_query():
    """Test querying links for a statute."""
    
    engine = create_engine(DATABASE_URL)
    
    print("="*60)
    print("TEST: RETRIEVAL QUERY")
    print("="*60)
    print("\nQuerying links for Section 2(1)...")
    
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT 
                case_citation,
                interpretation_type,
                authority,
                boost_factor,
                holding
            FROM interpretation_links
            WHERE statute_id = 'misrepresentation_act_1967_s2_1'
              AND verified = true
            ORDER BY boost_factor DESC, applicability_score DESC
            LIMIT 3
        """))
        
        links = result.fetchall()
        
        if not links:
            print("\n⚠️  No interpretive cases found for this statute")
        else:
            print(f"\nFound {len(links)} interpretive case(s):\n")
            for i, link in enumerate(links, 1):
                print(f"{i}. {link.case_citation}")
                print(f"   Type: {link.interpretation_type}")
                print(f"   Authority: {link.authority}")
                print(f"   Boost: {link.boost_factor}x")
                print(f"   Holding: {link.holding}")
                print()
    
    engine.dispose()

if __name__ == "__main__":
    print("\n🚀 WEEK 4 - INTERPRETATION LINK CREATION DEMO\n")
    
    # Create a sample link
    create_sample_link()
    
    # Show all links
    show_all_links()
    
    # Test retrieval
    test_retrieval_query()
    
    print("="*60)
    print("✅ DEMO COMPLETE!")
    print("="*60)
    print("\nNext steps:")
    print("  1. Review the link that was created")
    print("  2. Create more links for other statutes")
    print("  3. Test hybrid retrieval with interpretation boosting")
    print("  4. Build synthesis prompts")
