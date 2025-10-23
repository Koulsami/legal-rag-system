"""
Insert 41 interpretation links with all required fields.
"""

from src.database.connection import get_session
from sqlalchemy import text
from datetime import datetime
import uuid

db = get_session()

# All 41 links with complete data
links = [
    ('misrepresentation_act_1967_s2_1', '2000_sghc_134', '[2000] SGHC 134', 'SGHC', 2000, 'CLARIFY', 'PERSUASIVE', 2.0),
    ('misrepresentation_act_1967_s2_1', '2003_sgca_27', '[2003] SGCA 27', 'SGCA', 2003, 'CLARIFY', 'BINDING', 2.8),
    ('misrepresentation_act_1967_s1', '2005_sgca_25', '[2005] SGCA 25', 'SGCA', 2005, 'CLARIFY', 'BINDING', 2.8),
    ('misrepresentation_act_1967_s3', '2007_sgca_22', '[2007] SGCA 22', 'SGCA', 2007, 'CLARIFY', 'BINDING', 2.8),
    ('misrepresentation_act_1967_s3', '2007_sgca_24', '[2007] SGCA 24', 'SGCA', 2007, 'CLARIFY', 'BINDING', 2.8),
    ('misrepresentation_act_1967_s2_1', '2010_sgca_41', '[2010] SGCA 41', 'SGCA', 2010, 'CLARIFY', 'BINDING', 2.8),
    ('misrepresentation_act_1967_s2_2', '2010_sgca_41', '[2010] SGCA 41', 'SGCA', 2010, 'CLARIFY', 'BINDING', 2.8),
    ('misrepresentation_act_1967_s2_1', '2011_sghc_170', '[2011] SGHC 170', 'SGHC', 2011, 'CLARIFY', 'PERSUASIVE', 2.0),
    ('misrepresentation_act_1967_s2_1', '2012_sghc_159', '[2012] SGHC 159', 'SGHC', 2012, 'CLARIFY', 'PERSUASIVE', 2.0),
    ('misrepresentation_act_1967_s3', '2013_sgca_41', '[2013] SGCA 41', 'SGCA', 2013, 'CLARIFY', 'BINDING', 2.8),
    ('misrepresentation_act_1967_s2_2', '2013_sghc_38', '[2013] SGHC 38', 'SGHC', 2013, 'CLARIFY', 'PERSUASIVE', 2.0),
    ('misrepresentation_act_1967_s2_1', '2014_sgca_62', '[2014] SGCA 62', 'SGCA', 2014, 'CLARIFY', 'BINDING', 2.8),
    ('misrepresentation_act_1967_s2_2', '2014_sgca_62', '[2014] SGCA 62', 'SGCA', 2014, 'CLARIFY', 'BINDING', 2.8),
    ('misrepresentation_act_1967_s2_1', '2014_sghc_1', '[2014] SGHC 1', 'SGHC', 2014, 'CLARIFY', 'PERSUASIVE', 2.0),
    ('misrepresentation_act_1967_s3', '2014_sghc_1', '[2014] SGHC 1', 'SGHC', 2014, 'APPLY', 'PERSUASIVE', 2.0),
    ('misrepresentation_act_1967_s2_1', '2015_sgca_22', '[2015] SGCA 22', 'SGCA', 2015, 'CLARIFY', 'BINDING', 2.8),
    ('misrepresentation_act_1967_s2_2', '2015_sgca_22', '[2015] SGCA 22', 'SGCA', 2015, 'CLARIFY', 'BINDING', 2.8),
    ('misrepresentation_act_1967_s2_2', '2015_sghc_116', '[2015] SGHC 116', 'SGHC', 2015, 'CLARIFY', 'PERSUASIVE', 2.0),
    ('misrepresentation_act_1967_s2_1', '2015_sghc_116', '[2015] SGHC 116', 'SGHC', 2015, 'CLARIFY', 'PERSUASIVE', 2.0),
    ('misrepresentation_act_1967_s2_1', '2016_sghc_116', '[2016] SGHC 116', 'SGHC', 2016, 'CLARIFY', 'PERSUASIVE', 2.0),
    ('misrepresentation_act_1967_s2_1', '2017_sghc_201', '[2017] SGHC 201', 'SGHC', 2017, 'CLARIFY', 'PERSUASIVE', 2.0),
    ('misrepresentation_act_1967_s2_1', '2019_sghc_165', '[2019] SGHC 165', 'SGHC', 2019, 'CLARIFY', 'PERSUASIVE', 2.0),
    ('misrepresentation_act_1967_s2_1', '2019_sghc_39', '[2019] SGHC 39', 'SGHC', 2019, 'CLARIFY', 'PERSUASIVE', 2.0),
    ('misrepresentation_act_1967_s1', '2020_sgca_48', '[2020] SGCA 48', 'SGCA', 2020, 'CLARIFY', 'BINDING', 2.9),
    ('misrepresentation_act_1967_s2_1', '2020_sghc_219', '[2020] SGHC 219', 'SGHC', 2020, 'CLARIFY', 'PERSUASIVE', 2.1),
    ('misrepresentation_act_1967_s2_1', '2021_sghc_193', '[2021] SGHC 193', 'SGHC', 2021, 'CLARIFY', 'PERSUASIVE', 2.1),
    ('misrepresentation_act_1967_s2_2', '2021_sghc_193', '[2021] SGHC 193', 'SGHC', 2021, 'CLARIFY', 'PERSUASIVE', 2.1),
    ('misrepresentation_act_1967_s2_1', '2021_sghc_246', '[2021] SGHC 246', 'SGHC', 2021, 'NARROW', 'PERSUASIVE', 2.1),
    ('misrepresentation_act_1967_s2_1', '2022_sgca_54', '[2022] SGCA 54', 'SGCA', 2022, 'BROAD', 'BINDING', 2.9),
    ('misrepresentation_act_1967_s2_1', '2023_sghc_124', '[2023] SGHC 124', 'SGHC', 2023, 'NARROW', 'PERSUASIVE', 2.1),
    ('misrepresentation_act_1967_s2_1', '2023_sghc_13', '[2023] SGHC 13', 'SGHC', 2023, 'CLARIFY', 'PERSUASIVE', 2.1),
    ('misrepresentation_act_1967_s2_1', '2023_sghc_171', '[2023] SGHC 171', 'SGHC', 2023, 'CLARIFY', 'PERSUASIVE', 2.1),
    ('misrepresentation_act_1967_s3', '2023_sghc_171', '[2023] SGHC 171', 'SGHC', 2023, 'CLARIFY', 'PERSUASIVE', 2.1),
    ('misrepresentation_act_1967_s2_1', '2023_sghc_73', '[2023] SGHC 73', 'SGHC', 2023, 'CLARIFY', 'PERSUASIVE', 2.1),
    ('misrepresentation_act_1967_s3', '2024_sghc_279', '[2024] SGHC 279', 'SGHC', 2024, 'NARROW', 'PERSUASIVE', 2.1),
    ('misrepresentation_act_1967_s2_1', '2024_sghc_279', '[2024] SGHC 279', 'SGHC', 2024, 'CLARIFY', 'PERSUASIVE', 2.1),
    ('misrepresentation_act_1967_s2_1', '2025_sghc_109', '[2025] SGHC 109', 'SGHC', 2025, 'CLARIFY', 'PERSUASIVE', 2.1),
    ('misrepresentation_act_1967_s2_2', '2025_sghc_109', '[2025] SGHC 109', 'SGHC', 2025, 'NARROW', 'PERSUASIVE', 2.1),
    ('misrepresentation_act_1967_s2_1', '2025_sghc_161', '[2025] SGHC 161', 'SGHC', 2025, 'CLARIFY', 'PERSUASIVE', 2.1),
    ('misrepresentation_act_1967_s2_2', '2025_sghc_86', '[2025] SGHC 86', 'SGHC', 2025, 'CLARIFY', 'PERSUASIVE', 2.1),
    ('misrepresentation_act_1967_s2_1', '2025_sghc_86', '[2025] SGHC 86', 'SGHC', 2025, 'CLARIFY', 'PERSUASIVE', 2.1),
]

inserted = 0
skipped = 0

print("📝 Inserting 41 interpretation links...")
print("=" * 60)

for statute_id, case_id, citation, court, year, interp_type, authority, boost in links:
    # Extract section name from statute_id
    if 's1' in statute_id:
        section = 's 1'
    elif 's2_1' in statute_id:
        section = 's 2(1)'
    elif 's2_2' in statute_id:
        section = 's 2(2)'
    elif 's2_3' in statute_id:
        section = 's 2(3)'
    elif 's3' in statute_id:
        section = 's 3'
    else:
        section = 'Unknown'
    
    try:
        db.execute(text("""
            INSERT INTO interpretation_links (
                id, statute_id, case_id,
                statute_name, statute_section,
                case_name, case_citation, case_para_no,
                court, year,
                interpretation_type, authority, holding,
                boost_factor,
                created_at, updated_at
            ) VALUES (
                :id, :statute_id, :case_id,
                :statute_name, :statute_section,
                :case_name, :case_citation, :case_para_no,
                :court, :year,
                :interpretation_type, :authority, :holding,
                :boost_factor,
                :created_at, :updated_at
            )
        """), {
            'id': str(uuid.uuid4()),
            'statute_id': statute_id,
            'case_id': case_id,
            'statute_name': 'Misrepresentation Act 1967',
            'statute_section': section,
            'case_name': f'Case {citation}',
            'case_citation': citation,
            'case_para_no': 1,
            'court': court,
            'year': year,
            'interpretation_type': interp_type,
            'authority': authority,
            'holding': f'Court {interp_type.lower()}ed the interpretation of {section}',
            'boost_factor': boost,
            'created_at': datetime.now(),
            'updated_at': datetime.now()
        })
        db.commit()
        inserted += 1
        print(f"✅ {citation} → {section} ({interp_type})")
        
    except Exception as e:
        db.rollback()
        if 'unique' in str(e).lower() or 'duplicate' in str(e).lower():
            skipped += 1
            print(f"⏭️  {citation} → {section} (duplicate)")
        else:
            print(f"❌ {citation}: {e}")

db.close()

print("\n" + "=" * 60)
print(f"✅ Inserted: {inserted}")
print(f"⏭️  Skipped: {skipped}")
print(f"📊 Total: {inserted + skipped}/41")
print("=" * 60)
