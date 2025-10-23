"""
Populate interpretation_links table with sample data
Matches YOUR existing InterpretationLink schema
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from datetime import datetime, timezone
from dotenv import load_dotenv
import logging

from src.database.connection import get_session
from src.database.models.interpretation_link import InterpretationLink

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_sample_links() -> list:
    """Create sample interpretation links matching YOUR schema"""
    
    sample_links = [
        # Example 1: Misrepresentation Act Section 2
        {
            'statute_id': 'sg_statute_misrep_act_s2',
            'case_id': 'sg_case_2013_sgca_36_para_158',
            'statute_name': 'Misrepresentation Act 1967',
            'statute_section': '2',
            'statute_text': 'Where a person has entered into a contract after a misrepresentation...',
            'case_name': 'Wee Chiaw Sek Anna v Ng Li-Ann Genevieve',
            'case_citation': '[2013] SGCA 36',
            'case_para_no': 158,
            'case_text': 'Section 2 of the Misrepresentation Act does not impose a general duty to disclose...',
            'court': 'SGCA',
            'year': 2013,
            'interpretation_type': 'NARROW',
            'authority': 'BINDING',
            'holding': 'Section 2 applies only to fiduciary relationships, not all contractual relationships',
            'fact_pattern_tags': ['silence', 'fiduciary_duty', 'contract'],
            'case_facts_summary': 'Sale of shares between family members with non-disclosure',
            'applicability_score': 0.9,
            'cause_of_action': 'misrepresentation',
            'sub_issues': ['duty_to_disclose', 'fiduciary_relationship'],
            'boost_factor': 2.8,
            'verified': True,
            'verified_by': 'legal_researcher_1',
            'verified_at': datetime.now(timezone.utc),
            'extraction_method': 'MANUAL',
            'extraction_confidence': 1.0,
            'notes': 'Landmark SGCA case on duty to disclose'
        },
        
        # Example 2: Patents Act Section 80
        {
            'statute_id': 'sg_statute_patents_act_s80',
            'case_id': 'sg_case_2020_sgca_50_para_45',
            'statute_name': 'Patents Act 1994',
            'statute_section': '80',
            'statute_text': 'In any proceedings for infringement of a patent, the defendant may apply...',
            'case_name': 'Lee Tat Development Pte Ltd v MCST Plan No 301',
            'case_citation': '[2020] SGCA 50',
            'case_para_no': 45,
            'case_text': 'The test for striking out under Section 80 requires "plainly and obviously" unsustainable...',
            'court': 'SGCA',
            'year': 2020,
            'interpretation_type': 'CLARIFY',
            'authority': 'BINDING',
            'holding': 'Clarified the "plain and obvious" test for striking out patent claims',
            'fact_pattern_tags': ['strike_out', 'patent_infringement', 'procedure'],
            'case_facts_summary': 'Application to strike out patent infringement claim',
            'applicability_score': 0.95,
            'cause_of_action': 'patent_infringement',
            'sub_issues': ['strike_out_test', 'pleadings'],
            'boost_factor': 2.5,
            'verified': True,
            'verified_by': 'legal_researcher_1',
            'verified_at': datetime.now(timezone.utc),
            'extraction_method': 'MANUAL',
            'extraction_confidence': 1.0,
            'notes': 'Key case on strike-out test'
        },
        
        # Example 3: ROC 2021
        {
            'statute_id': 'sg_rule_roc_2021_o9_r16',
            'case_id': 'sg_case_2022_sghc_100_para_23',
            'statute_name': 'Rules of Court 2021',
            'statute_section': 'Order 9 Rule 16',
            'statute_text': 'The Court may strike out any pleading or part thereof...',
            'case_name': 'ABC Co Ltd v XYZ Ltd',
            'case_citation': '[2022] SGHC 100',
            'case_para_no': 23,
            'case_text': 'Order 9 Rule 16 must be read harmoniously with the overriding objective...',
            'court': 'SGHC',
            'year': 2022,
            'interpretation_type': 'PURPOSIVE',
            'authority': 'PERSUASIVE',
            'holding': 'Emphasized purposive approach to procedural rules',
            'fact_pattern_tags': ['civil_procedure', 'strike_out', 'pleadings'],
            'case_facts_summary': 'Application to strike out allegedly defective pleadings',
            'applicability_score': 0.85,
            'cause_of_action': 'civil_procedure',
            'sub_issues': ['pleading_defects', 'procedural_rules'],
            'boost_factor': 2.0,
            'verified': True,
            'verified_by': 'legal_researcher_1',
            'verified_at': datetime.now(timezone.utc),
            'extraction_method': 'MANUAL',
            'extraction_confidence': 1.0,
            'notes': 'Illustrates purposive interpretation'
        }
    ]
    
    return sample_links


def populate_links(session):
    """Populate database with sample interpretation links"""
    
    sample_links = create_sample_links()
    
    logger.info(f"Populating {len(sample_links)} interpretation links...")
    
    added_count = 0
    skipped_count = 0
    
    for link_data in sample_links:
        # Check if exists
        existing = session.query(InterpretationLink).filter_by(
            statute_id=link_data['statute_id'],
            case_id=link_data['case_id']
        ).first()
        
        if existing:
            logger.info(f"Skipping existing: {link_data['statute_id']} -> {link_data['case_id']}")
            skipped_count += 1
            continue
        
        # Create new link
        link = InterpretationLink(**link_data)
        session.add(link)
        added_count += 1
        
        logger.info(f"Added: {link_data['statute_id']} -> {link_data['case_id']}")
    
    # Commit
    session.commit()
    
    logger.info(f"✅ Added {added_count} links, skipped {skipped_count} existing")
    
    # Verify
    total_links = session.query(InterpretationLink).count()
    logger.info(f"Total interpretation links in database: {total_links}")


def main():
    """Main function"""
    
    logger.info("Populating interpretation_links table...")
    
    session = get_session()
    
    populate_links(session)
    
    logger.info("🚀 Interpretation links populated!")


if __name__ == "__main__":
    main()
