"""
Insert the 41 extracted links one by one, skipping duplicates.
"""

from src.database.connection import get_session
from sqlalchemy import text
import uuid
from datetime import datetime

# The 41 links that were extracted
links_data = [
    ('misrepresentation_act_1967_s2_1', '2000_sghc_134', '[2000] SGHC 134', 'SGHC', 2000, 'CLARIFY', 2.0),
    ('misrepresentation_act_1967_s2_1', '2003_sgca_27', '[2003] SGCA 27', 'SGCA', 2003, 'CLARIFY', 2.8),
    ('misrepresentation_act_1967_s1', '2005_sgca_25', '[2005] SGCA 25', 'SGCA', 2005, 'CLARIFY', 2.8),
    ('misrepresentation_act_1967_s3', '2007_sgca_22', '[2007] SGCA 22', 'SGCA', 2007, 'CLARIFY', 2.8),
    ('misrepresentation_act_1967_s3', '2007_sgca_24', '[2007] SGCA 24', 'SGCA', 2007, 'CLARIFY', 2.8),
    ('misrepresentation_act_1967_s2_1', '2010_sgca_41', '[2010] SGCA 41', 'SGCA', 2010, 'CLARIFY', 2.8),
    ('misrepresentation_act_1967_s2_2', '2010_sgca_41', '[2010] SGCA 41', 'SGCA', 2010, 'CLARIFY', 2.8),
    ('misrepresentation_act_1967_s2_1', '2011_sghc_170', '[2011] SGHC 170', 'SGHC', 2011, 'CLARIFY', 2.0),
    ('misrepresentation_act_1967_s2_1', '2012_sghc_159', '[2012] SGHC 159', 'SGHC', 2012, 'CLARIFY', 2.0),
    ('misrepresentation_act_1967_s3', '2013_sgca_41', '[2013] SGCA 41', 'SGCA', 2013, 'CLARIFY', 2.8),
    ('misrepresentation_act_1967_s2_2', '2013_sghc_38', '[2013] SGHC 38', 'SGHC', 2013, 'CLARIFY', 2.0),
    ('misrepresentation_act_1967_s2_1', '2014_sgca_62', '[2014] SGCA 62', 'SGCA', 2014, 'CLARIFY', 2.8),
    ('misrepresentation_act_1967_s2_2', '2014_sgca_62', '[2014] SGCA 62', 'SGCA', 2014, 'CLARIFY', 2.8),
    ('misrepresentation_act_1967_s2_1', '2014_sghc_1', '[2014] SGHC 1', 'SGHC', 2014, 'CLARIFY', 2.0),
    ('misrepresentation_act_1967_s3', '2014_sghc_1', '[2014] SGHC 1', 'SGHC', 2014, 'APPLY', 2.0),
    ('misrepresentation_act_1967_s2_1', '2015_sgca_22', '[2015] SGCA 22', 'SGCA', 2015, 'CLARIFY', 2.8),
    ('misrepresentation_act_1967_s2_2', '2015_sgca_22', '[2015] SGCA 22', 'SGCA', 2015, 'CLARIFY', 2.8),
    ('misrepresentation_act_1967_s2_2', '2015_sghc_116', '[2015] SGHC 116', 'SGHC', 2015, 'CLARIFY', 2.0),
    ('misrepresentation_act_1967_s2_1', '2015_sghc_116', '[2015] SGHC 116', 'SGHC', 2015, 'CLARIFY', 2.0),
    ('misrepresentation_act_1967_s2_1', '2016_sghc_116', '[2016] SGHC 116', 'SGHC', 2016, 'CLARIFY', 2.0),
    ('misrepresentation_act_1967_s2_1', '2017_sghc_201', '[2017] SGHC 201', 'SGHC', 2017, 'CLARIFY', 2.0),
    ('misrepresentation_act_1967_s2_1', '2019_sghc_165', '[2019] SGHC 165', 'SGHC', 2019, 'CLARIFY', 2.0),
    ('misrepresentation_act_1967_s2_1', '2019_sghc_39', '[2019] SGHC 39', 'SGHC', 2019, 'CLARIFY', 2.0),
    ('misrepresentation_act_1967_s1', '2020_sgca_48', '[2020] SGCA 48', 'SGCA', 2020, 'CLARIFY', 2.9),
    ('misrepresentation_act_1967_s2_1', '2020_sghc_219', '[2020] SGHC 219', 'SGHC', 2020, 'CLARIFY', 2.1),
    ('misrepresentation_act_1967_s2_1', '2021_sghc_193', '[2021] SGHC 193', 'SGHC', 2021, 'CLARIFY', 2.1),
    ('misrepresentation_act_1967_s2_2', '2021_sghc_193', '[2021] SGHC 193', 'SGHC', 2021, 'CLARIFY', 2.1),
    ('misrepresentation_act_1967_s2_1', '2021_sghc_246', '[2021] SGHC 246', 'SGHC', 2021, 'NARROW', 2.1),
    ('misrepresentation_act_1967_s2_1', '2022_sgca_54', '[2022] SGCA 54', 'SGCA', 2022, 'BROAD', 2.9),
    ('misrepresentation_act_1967_s2_1', '2023_sghc_124', '[2023] SGHC 124', 'SGHC', 2023, 'NARROW', 2.1),
    ('misrepresentation_act_1967_s2_1', '2023_sghc_13', '[2023] SGHC 13', 'SGHC', 2023, 'CLARIFY', 2.1),
    ('misrepresentation_act_1967_s2_1', '2023_sghc_171', '[2023] SGHC 171', 'SGHC', 2023, 'CLARIFY', 2.1),
    ('misrepresentation_act_1967_s3', '2023_sghc_171', '[2023] SGHC 171', 'SGHC', 2023, 'CLARIFY', 2.1),
    ('misrepresentation_act_1967_s2_1', '2023_sghc_73', '[2023] SGHC 73', 'SGHC', 2023, 'CLARIFY', 2.1),
    ('misrepresentation_act_1967_s3', '2024_sghc_279', '[2024] SGHC 279', 'SGHC', 2024, 'NARROW', 2.1),
    ('misrepresentation_act_1967_s2_1', '2024_sghc_279', '[2024] SGHC 279', 'SGHC', 2024, 'CLARIFY', 2.1),
    ('misrepresentation_act_1967_s2_1', '2025_sghc_109', '[2025] SGHC 109', 'SGHC', 2025, 'CLARIFY', 2.1),
    ('misrepresentation_act_1967_s2_2', '2025_sghc_109', '[2025] SGHC 109', 'SGHC', 2025, 'NARROW', 2.1),
    ('misrepresentation_act_1967_s2_1', '2025_sghc_161', '[2025] SGHC 161', 'SGHC', 2025, 'CLARIFY', 2.1),
    ('misrepresentation_act_1967_s2_2', '2025_sghc_86', '[2025] SGHC 86', 'SGHC', 2025, 'CLARIFY', 2.1),
    ('misrepresentation_act_1967_s2_1', '2025_sghc_86', '[2025] SGHC 86', 'SGHC', 2025, 'CLARIFY', 2.1),
]

db = get_session()

inserted = 0
skipped = 0

print("📝 Inserting interpretation links...")
print("=" * 60)

for statute_id, case_id, citation, court, year, interp_type, boost in links_data:
    try:
        db.execute(text("""
            INSERT INTO interpretation_links (
                id, statute_id, case_id,
                statute_name, statute_section,
                case_citation, court, year,
                interpretation_type, authority,
                boost_factor, verified,
                extraction_method, confidence,
                created_at
            ) VALUES (
                :id, :statute_id, :case_id,
                :statute_name, :statute_section,
                :case_citation, :court, :year,
                :interpretation_type, :authority,
                :boost_factor, :verified,
                :extraction_method, :confidence,
                :created_at
            )
        """), {
            'id': str(uuid.uuid4()),
            'statute_id': statute_id,
            'case_id': case_id,
            'statute_name': 'Misrepresentation Act 1967',
            'statute_section': statute_id.split('_')[-1].replace('s', 's '),
            'case_citation': citation,
            'court': court,
            'year': year,
            'interpretation_type': interp_type,
            'authority': 'BINDING' if 'sgca' in court.lower() else 'PERSUASIVE',
            'boost_factor': boost,
            'verified': True,
            'extraction_method': 'RULE_BASED',
            'confidence': 0.8,
            'created_at': datetime.now()
        })
        db.commit()
        inserted += 1
        print(f"✅ {citation} → {statute_id.split('_')[-1]}")
    except Exception as e:
        db.rollback()
        if 'unique' in str(e).lower() or 'duplicate' in str(e).lower():
            skipped += 1
            print(f"⏭️  {citation} (already exists)")
        else:
            print(f"❌ {citation}: {e}")

db.close()

print("\n" + "=" * 60)
print(f"✅ Inserted: {inserted}")
print(f"⏭️  Skipped: {skipped}")
print(f"📊 Total: {inserted + skipped}")
print("=" * 60)
