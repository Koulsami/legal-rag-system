"""
Hallucination Detection Examples
Week 5 Day 3

Demonstrates:
1. Detecting verified interpretation claims
2. Detecting unverified claims
3. Detecting hallucinated claims
4. Integration with full validation pipeline
5. Removing hallucinated sentences
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from validation.hallucination_detector import HallucinationDetector, detect_hallucinations
from unittest.mock import Mock, MagicMock
import json


def example_verified_claims():
    """
    Example 1: All claims verified in database (ideal case)
    Expected: 0% hallucination rate, all claims verified
    """
    print("=" * 80)
    print("EXAMPLE 1: All Claims Verified (Ideal Case)")
    print("=" * 80)
    
    answer = """
    **Statute:** Misrepresentation Act, Section 2 states "No person shall be liable 
    for misrepresentation unless there was a duty to disclose."
    
    **Judicial Interpretation:** In Wee Chiaw Sek Anna v Ng Li-Ann Genevieve 
    [2013] SGCA 36, ¶158, the Court held that Section 2 of the Misrepresentation Act 
    applies only to fiduciary relationships where a duty of disclosure exists.
    
    **Synthesis:** While the statute appears to apply broadly, case law has limited 
    it to trust-based relationships. The court interpreted "duty to disclose" narrowly 
    to mean fiduciary duties rather than general disclosure obligations.
    
    **Practical Effect:** In practice, silence is only misrepresentation in fiduciary 
    contexts like trustee-beneficiary or solicitor-client relationships.
    """
    
    # Setup mock database that verifies the claim
    mock_db = Mock()
    mock_result = MagicMock()
    mock_result.interpretation_type = "NARROW"
    mock_result.authority_level = "BINDING"
    mock_result.boost_factor = 2.5
    mock_result.confidence = 0.95
    mock_db.execute.return_value.fetchone.return_value = mock_result
    
    # Detect hallucinations
    detector = HallucinationDetector(mock_db)
    report = detector.detect_hallucinations(answer)
    
    print(f"\n📊 HALLUCINATION REPORT:")
    print(f"Total Claims: {report.total_claims}")
    print(f"Verified: {report.verified_claims} ✅")
    print(f"Unverified: {report.unverified_claims}")
    print(f"Hallucinated: {report.hallucinated_claims}")
    print(f"\nHallucination Rate: {report.hallucination_rate:.1%} (Target: ≤ 5%)")
    print(f"Verification Rate: {report.verification_rate:.1%}")
    print(f"\nPassed: {'✅ YES' if report.passed else '❌ NO'}")
    print(f"Needs Review: {'⚠️ YES' if report.needs_review else '✅ NO'}")
    
    print(f"\n🔍 EXTRACTED CLAIMS:")
    for i, claim in enumerate(report.claims, 1):
        print(f"\n  Claim {i}:")
        print(f"    Case: {claim.case_name} {claim.case_citation}")
        print(f"    Statute: {claim.statute_name}, Section {claim.statute_section}")
        print(f"    Status: {claim.status.value.upper()}")
        print(f"    Confidence: {claim.confidence:.2f}")
        if claim.status.value == 'verified':
            print(f"    DB Match:")
            print(f"      Type: {claim.db_interpretation_type}")
            print(f"      Authority: {claim.db_authority_level}")
            print(f"      Boost Factor: {claim.db_boost_factor}×")
    print("\n")


def example_unverified_claims():
    """
    Example 2: Claims not in database (needs manual verification)
    Expected: 0% hallucination, but low verification rate
    """
    print("=" * 80)
    print("EXAMPLE 2: Unverified Claims (Not in Database)")
    print("=" * 80)
    
    answer = """
    **Statute:** Defamation Act, Section 7 provides the truth defense.
    
    **Interpretation:** In Lim v Singapore Press Holdings [2015] SGCA 33, ¶45, 
    the Court held that Section 7 of the Defamation Act requires demonstrable 
    social utility, not mere public interest.
    
    **Synthesis:** While the statute says "public benefit," case law has narrowed 
    this to require proof of positive societal impact.
    
    **Practical Effect:** Defendants must show material public benefit, not just 
    that the matter was newsworthy.
    """
    
    # Setup mock database that returns None (not found)
    mock_db = Mock()
    mock_db.execute.return_value.fetchone.return_value = None
    
    detector = HallucinationDetector(mock_db)
    report = detector.detect_hallucinations(answer)
    
    print(f"\n📊 HALLUCINATION REPORT:")
    print(f"Total Claims: {report.total_claims}")
    print(f"Verified: {report.verified_claims}")
    print(f"Unverified: {report.unverified_claims} ⚠️")
    print(f"Hallucinated: {report.hallucinated_claims}")
    print(f"\nHallucination Rate: {report.hallucination_rate:.1%}")
    print(f"Verification Rate: {report.verification_rate:.1%} ⚠️ LOW")
    print(f"\nPassed: {'✅ YES' if report.passed else '❌ NO'}")
    print(f"Needs Review: {'⚠️ YES' if report.needs_review else '✅ NO'}")
    
    print(f"\n⚠️ RECOMMENDATION:")
    print(f"  • Unverified claims should be manually reviewed")
    print(f"  • Add verified interpretation links to database")
    print(f"  • Re-run detection after adding links")
    print("\n")


def example_hallucinated_claims():
    """
    Example 3: Completely fabricated interpretation claims
    Expected: High hallucination rate, should fail
    """
    print("=" * 80)
    print("EXAMPLE 3: Hallucinated Claims (Fabricated)")
    print("=" * 80)
    
    answer = """
    **Statute:** Privacy Act, Section 12 protects personal data.
    
    **Interpretation:** In Fake Case v Another Fake Party [2025] SGCA 999, ¶200, 
    the Court held that Section 12 of the Privacy Act applies to all online 
    communications without exception.
    
    **Synthesis:** This represents a broad interpretation that extends privacy 
    protections to digital communications.
    
    **Practical Effect:** Companies must obtain consent before any data processing.
    """
    
    # Setup mock database that returns None
    mock_db = Mock()
    mock_db.execute.return_value.fetchone.return_value = None
    
    # Create context that doesn't mention the statute
    retrieved_context = {
        'case_paragraphs': [
            {
                'citation': '[2025] SGCA 999',
                'text': 'This case discusses contract law, not privacy.'
            }
        ]
    }
    
    detector = HallucinationDetector(mock_db)
    report = detector.detect_hallucinations(answer, retrieved_context)
    
    print(f"\n📊 HALLUCINATION REPORT:")
    print(f"Total Claims: {report.total_claims}")
    print(f"Verified: {report.verified_claims}")
    print(f"Unverified: {report.unverified_claims}")
    print(f"Hallucinated: {report.hallucinated_claims} ❌ CRITICAL")
    print(f"\nHallucination Rate: {report.hallucination_rate:.1%} ❌ EXCEEDS 5% THRESHOLD")
    print(f"Verification Rate: {report.verification_rate:.1%}")
    print(f"\nPassed: {'✅ YES' if report.passed else '❌ NO'}")
    print(f"Needs Review: {'⚠️ YES' if report.needs_review else '✅ NO'}")
    
    print(f"\n🚨 FLAGGED SENTENCES:")
    for sentence in report.flagged_sentences:
        print(f"  • {sentence[:100]}...")
    
    print(f"\n❌ ACTION REQUIRED:")
    print(f"  • Answer contains hallucinated interpretation claims")
    print(f"  • Remove flagged sentences or regenerate answer")
    print(f"  • Do NOT present this answer to user")
    print("\n")


def example_full_validation_pipeline():
    """
    Example 4: Complete validation pipeline (Day 1 + Day 2 + Day 3)
    Shows integration of all validators
    """
    print("=" * 80)
    print("EXAMPLE 4: Full Validation Pipeline (Days 1-3 Integration)")
    print("=" * 80)
    
    answer = """
    **Statute:** Misrepresentation Act, Section 2
    
    **Interpretation:** In Wee [2013] SGCA 36, ¶158, the Court held that 
    Section 2 applies only to fiduciary relationships. [INTERPRETS STATUTE]
    
    **Synthesis:** While the statute appears broad, case law has limited it 
    to trust-based relationships.
    
    **Practical Effect:** In practice, silence is only misrepresentation in 
    fiduciary contexts.
    """
    
    # Setup mock DB for verified claim
    mock_db = Mock()
    mock_result = MagicMock()
    mock_result.interpretation_type = "NARROW"
    mock_result.authority_level = "BINDING"
    mock_result.boost_factor = 2.5
    mock_result.confidence = 0.95
    mock_db.execute.return_value.fetchone.return_value = mock_result
    
    print(f"\n🔄 VALIDATION PIPELINE:\n")
    
    # Stage 1: Synthesis Quality (Day 2)
    print("  [1/3] Synthesis Quality Scorer...")
    from validation.synthesis_quality_scorer import SynthesisQualityScorer
    synthesis_scorer = SynthesisQualityScorer()
    synthesis_result = synthesis_scorer.score_answer(answer)
    print(f"        Score: {synthesis_result.overall_score:.2f}")
    print(f"        Status: {'✅ PASS' if synthesis_result.passed else '❌ FAIL'}")
    
    # Stage 2: Citation Validation (Day 1)
    print(f"\n  [2/3] Citation Validator...")
    print(f"        Checking citations exist...")
    print(f"        Status: ✅ PASS (mock)")
    
    # Stage 3: Hallucination Detection (Day 3)
    print(f"\n  [3/3] Hallucination Detector...")
    detector = HallucinationDetector(mock_db)
    hallucination_report = detector.detect_hallucinations(answer)
    print(f"        Verified Claims: {hallucination_report.verified_claims}/{hallucination_report.total_claims}")
    print(f"        Hallucination Rate: {hallucination_report.hallucination_rate:.1%}")
    print(f"        Status: {'✅ PASS' if hallucination_report.passed else '❌ FAIL'}")
    
    # Final Decision
    print(f"\n📊 FINAL VALIDATION RESULT:")
    all_passed = (
        synthesis_result.passed and
        hallucination_report.passed
    )
    print(f"  Overall Status: {'✅ ALL CHECKS PASSED' if all_passed else '❌ FAILED'}")
    
    if all_passed:
        print(f"  Decision: ✅ SEND TO USER")
    else:
        print(f"  Decision: ⚠️ ROUTE TO REVIEW QUEUE")
    
    print(f"\n  Quality Metrics:")
    print(f"    • Synthesis Quality: {synthesis_result.overall_score:.2f} (≥ 0.7)")
    print(f"    • Verification Rate: {hallucination_report.verification_rate:.1%}")
    print(f"    • Hallucination Rate: {hallucination_report.hallucination_rate:.1%} (≤ 5%)")
    print("\n")


def example_remove_hallucinated_content():
    """
    Example 5: Removing hallucinated sentences from answer
    """
    print("=" * 80)
    print("EXAMPLE 5: Removing Hallucinated Content")
    print("=" * 80)
    
    original_answer = """
    This is a correct statement about the law. In Fake Case [2025] SGCA 999, 
    the court held that Section 99 applies universally. This is another 
    correct statement. The practical effect is significant.
    """
    
    # Mock detection that flags the fake case sentence
    mock_db = Mock()
    mock_db.execute.return_value.fetchone.return_value = None
    
    detector = HallucinationDetector(mock_db)
    report = detector.detect_hallucinations(original_answer)
    
    print(f"\n📄 ORIGINAL ANSWER:")
    print(original_answer)
    
    print(f"\n🚨 FLAGGED SENTENCES: {len(report.flagged_sentences)}")
    for sentence in report.flagged_sentences:
        print(f"  • {sentence[:80]}...")
    
    # Remove hallucinated sentences
    cleaned_answer = detector.remove_hallucinated_sentences(original_answer, report)
    
    print(f"\n✅ CLEANED ANSWER:")
    print(cleaned_answer)
    
    print(f"\n📊 RESULT:")
    print(f"  • Removed {len(report.flagged_sentences)} hallucinated sentence(s)")
    print(f"  • Answer safe to present to user")
    print("\n")


def example_json_export():
    """
    Example 6: Exporting detection results as JSON
    """
    print("=" * 80)
    print("EXAMPLE 6: JSON Export for API Integration")
    print("=" * 80)
    
    answer = "In Wee [2013] SGCA 36, Court held Section 2 of Misrepresentation Act applies."
    
    # Mock verified claim
    mock_db = Mock()
    mock_result = MagicMock()
    mock_result.interpretation_type = "NARROW"
    mock_result.authority_level = "BINDING"
    mock_result.boost_factor = 2.5
    mock_result.confidence = 0.95
    mock_db.execute.return_value.fetchone.return_value = mock_result
    
    detector = HallucinationDetector(mock_db)
    report = detector.detect_hallucinations(answer)
    
    # Export as JSON
    json_output = json.dumps(report.to_dict(), indent=2)
    
    print(f"\n📤 JSON OUTPUT:")
    print(json_output)
    
    print(f"\n💡 USE CASE:")
    print(f"  • API endpoint returns this JSON")
    print(f"  • Frontend displays verification status")
    print(f"  • Downstream systems consume metrics")
    print("\n")


def main():
    """Run all examples"""
    print("\n🚀 HALLUCINATION DETECTION EXAMPLES\n")
    
    example_verified_claims()
    example_unverified_claims()
    example_hallucinated_claims()
    example_full_validation_pipeline()
    example_remove_hallucinated_content()
    example_json_export()
    
    print("=" * 80)
    print("✅ All examples completed!")
    print("=" * 80)


if __name__ == '__main__':
    main()
