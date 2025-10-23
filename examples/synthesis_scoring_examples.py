"""
Synthesis Quality Scoring Examples
Week 5 Day 2

Demonstrates:
1. Perfect 4-step synthesis (score ≥ 0.9)
2. Good synthesis (score ≥ 0.7)
3. Weak synthesis (score < 0.7)
4. Integration with citation validator
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from validation.synthesis_quality_scorer import SynthesisQualityScorer
import json


def example_perfect_synthesis():
    """
    Example of a perfect answer with all 4 sections.
    Expected score: ≥ 0.9
    """
    print("=" * 80)
    print("EXAMPLE 1: Perfect Synthesis (Expected Score ≥ 0.9)")
    print("=" * 80)
    
    answer = """
    **Statute:** "No person shall be liable in an action for defamation in respect of 
    the publication of any matter if the defendant proves that the matter was true and 
    that it was for the public benefit that it should be published." 
    (Defamation Act, Section 7)
    
    **Judicial Interpretation:** The Court of Appeal in Lim v Singapore Press Holdings 
    [2015] SGCA 33, ¶45 held that "public benefit" requires more than mere public 
    interest—there must be demonstrable social utility in the disclosure. The court 
    stated that "the defendant must establish not only that the statement is true, but 
    that its publication serves a genuine public purpose beyond satisfying curiosity."
    [INTERPRETS STATUTE: Defamation Act, Section 7]
    
    **Synthesis:** While the statute appears to create a broad defense based on truth 
    and public interest, case law has significantly narrowed this by requiring proof of 
    positive public benefit. The plain text suggests truth combined with any public 
    interest suffices, but binding precedent limits this to cases where publication 
    serves a demonstrable public good. The court's interpretation transforms a seemingly 
    objective test (truth + public interest) into a more demanding standard requiring 
    affirmative proof of social utility.
    
    **Practical Effect:** In practice, this means defendants cannot rely solely on 
    proving the truth of their statements. They must also demonstrate that publishing 
    the information materially benefited society—for instance, exposing corruption or 
    misconduct affecting public welfare. This raises the bar significantly for the 
    defense and protects individuals from having true but purely private matters 
    disclosed without genuine public justification.
    """
    
    scorer = SynthesisQualityScorer()
    result = scorer.score_answer(answer)
    
    print(f"\n📊 SCORE BREAKDOWN:")
    print(f"Overall Score: {result.overall_score:.3f} {'✅ PASS' if result.passed else '❌ FAIL'}")
    print(f"\nSection Scores:")
    print(f"  • Statute (25%):         {result.statute_score:.3f}")
    print(f"  • Interpretation (25%):  {result.interpretation_score:.3f}")
    print(f"  • Synthesis (30%):       {result.synthesis_score:.3f} ⭐ HIGHEST WEIGHT")
    print(f"  • Practical Effect (20%): {result.practical_effect_score:.3f}")
    
    print(f"\n📋 Feedback:")
    for feedback_item in result.feedback:
        print(f"  • {feedback_item}")
    
    print(f"\n🔍 Detected Patterns:")
    print(json.dumps(result.detected_patterns, indent=2))
    print("\n")


def example_good_synthesis():
    """
    Example of a good answer (passes threshold).
    Expected score: 0.7 - 0.85
    """
    print("=" * 80)
    print("EXAMPLE 2: Good Synthesis (Expected Score 0.7 - 0.85)")
    print("=" * 80)
    
    answer = """
    **Statute:** The Rules of Court 2021, Order 9 Rule 16 allows the court to strike 
    out claims that are "plainly or obviously unsustainable" or disclose "no reasonable 
    cause of action."
    
    **Interpretation:** In Gabriel Peter & Partners v Wee Chong Jin [1997] SGCA 58, ¶21, 
    the Court of Appeal held that the test requires the claim to be "obviously 
    unsustainable" on its face. The court stated it should only strike out in clear cases.
    
    **Synthesis:** While the statutory language appears to give broad discretion, case 
    law has limited this to cases where failure is obvious and certain. The court 
    interpreted the provision narrowly to preserve access to justice.
    
    In practice, this means courts rarely strike out claims at this stage. Claimants 
    get the benefit of the doubt unless the case is manifestly hopeless.
    """
    
    scorer = SynthesisQualityScorer()
    result = scorer.score_answer(answer)
    
    print(f"\n📊 SCORE BREAKDOWN:")
    print(f"Overall Score: {result.overall_score:.3f} {'✅ PASS' if result.passed else '❌ FAIL'}")
    print(f"\nSection Scores:")
    print(f"  • Statute (25%):         {result.statute_score:.3f}")
    print(f"  • Interpretation (25%):  {result.interpretation_score:.3f}")
    print(f"  • Synthesis (30%):       {result.synthesis_score:.3f}")
    print(f"  • Practical Effect (20%): {result.practical_effect_score:.3f}")
    
    if result.missing_sections:
        print(f"\n⚠️ Missing Sections: {', '.join(result.missing_sections)}")
    
    print(f"\n📋 Feedback:")
    for feedback_item in result.feedback:
        print(f"  • {feedback_item}")
    print("\n")


def example_weak_synthesis():
    """
    Example of a weak answer (fails threshold).
    Expected score: < 0.7
    """
    print("=" * 80)
    print("EXAMPLE 3: Weak Synthesis (Expected Score < 0.7)")
    print("=" * 80)
    
    answer = """
    Under Singapore law, courts can strike out claims under the Rules of Court. 
    This has been discussed in various cases. The threshold is quite high.
    
    The case of Gabriel Peter held that only obviously unsustainable claims should 
    be struck out. Courts are careful about this.
    
    So basically, it's hard to get a claim struck out. You need to have a really 
    bad case for that to happen.
    """
    
    scorer = SynthesisQualityScorer()
    result = scorer.score_answer(answer)
    
    print(f"\n📊 SCORE BREAKDOWN:")
    print(f"Overall Score: {result.overall_score:.3f} {'✅ PASS' if result.passed else '❌ FAIL'}")
    print(f"\nSection Scores:")
    print(f"  • Statute (25%):         {result.statute_score:.3f}")
    print(f"  • Interpretation (25%):  {result.interpretation_score:.3f}")
    print(f"  • Synthesis (30%):       {result.synthesis_score:.3f}")
    print(f"  • Practical Effect (20%): {result.practical_effect_score:.3f}")
    
    print(f"\n⚠️ Missing Sections: {', '.join(result.missing_sections)}")
    
    print(f"\n📋 Feedback (How to Improve):")
    for feedback_item in result.feedback:
        print(f"  • {feedback_item}")
    print("\n")


def example_integration_with_validator():
    """
    Example showing integration with EnhancedCitationValidator.
    
    Full pipeline:
    1. Score synthesis quality
    2. Validate citations
    3. Verify interpretation links
    4. Route to review if needed
    """
    print("=" * 80)
    print("EXAMPLE 4: Integration with Citation Validator")
    print("=" * 80)
    
    answer = """
    **Statute:** Misrepresentation Act, Section 2 states "No person shall be liable for 
    misrepresentation unless there was a duty to disclose."
    
    **Interpretation:** In Wee Chiaw Sek Anna v Ng Li-Ann Genevieve [2013] SGCA 36, ¶158, 
    the Court held that this applies only to fiduciary relationships.
    [INTERPRETS STATUTE: Misrepresentation Act, Section 2]
    
    **Synthesis:** While the statute appears to apply broadly, case law has limited it 
    to trust-based relationships. The court interpreted "duty to disclose" narrowly.
    
    **Practical Effect:** In practice, silence is only misrepresentation in fiduciary 
    contexts like trustee-beneficiary or solicitor-client relationships.
    """
    
    # Step 1: Score synthesis quality
    scorer = SynthesisQualityScorer()
    synthesis_result = scorer.score_answer(answer)
    
    print(f"\n📊 SYNTHESIS QUALITY:")
    print(f"Score: {synthesis_result.overall_score:.3f} {'✅ PASS' if synthesis_result.passed else '❌ FAIL'}")
    
    # Step 2: Check if interpretation link claim exists
    print(f"\n🔗 INTERPRETATION LINK VALIDATION:")
    if '[INTERPRETS STATUTE]' in answer or 'INTERPRETS STATUTE' in answer:
        print("  ✅ Found [INTERPRETS STATUTE] marker")
        print("  📋 Claimed interpretation:")
        print("      Case: Wee Chiaw Sek Anna v Ng Li-Ann Genevieve [2013] SGCA 36")
        print("      Statute: Misrepresentation Act, Section 2")
        print("      Type: NARROW (limits to fiduciary relationships)")
        print("  ⚠️ Would validate against interpretation_links database")
        print("      (EnhancedCitationValidator.validate_interpretation_link())")
    
    # Step 3: Routing decision
    print(f"\n🎯 ROUTING DECISION:")
    if synthesis_result.passed:
        print("  ✅ ROUTE TO USER (synthesis score ≥ 0.7)")
    else:
        print("  ⚠️ ROUTE TO REVIEW QUEUE (synthesis score < 0.7)")
        print("  📋 Review needed for:")
        for section in synthesis_result.missing_sections:
            print(f"      • {section}")
    
    print(f"\n💡 NEXT STEPS:")
    print("  1. Validate all citations exist in corpus (Stage 1)")
    print("  2. Check text alignment (Stage 2)")
    print("  3. Verify propositional support (Stage 3)")
    print("  4. Validate jurisdiction (Stage 4)")
    print("  5. Check temporal validity (Stage 5)")
    print("  6. Verify interpretation link in DB (Stage 6)")
    print("\n")


def example_missing_synthesis_penalty():
    """
    Example showing that missing SYNTHESIS gets the highest penalty (30% weight).
    """
    print("=" * 80)
    print("EXAMPLE 5: Missing Synthesis = Highest Penalty (30% weight)")
    print("=" * 80)
    
    answer_no_synthesis = """
    **Statute:** Defamation Act, Section 7 provides the truth defense with public benefit.
    
    **Interpretation:** Court held in Lim v SPH [2015] SGCA 33, ¶45 about public benefit 
    requirements.
    
    **Practical Effect:** This affects how defendants structure their defamation defenses 
    in Singapore courts.
    """
    
    scorer = SynthesisQualityScorer()
    result = scorer.score_answer(answer_no_synthesis)
    
    print(f"\n📊 SCORE BREAKDOWN:")
    print(f"Overall Score: {result.overall_score:.3f} {'✅ PASS' if result.passed else '❌ FAIL'}")
    print(f"\nSection Scores:")
    print(f"  • Statute (25%):         {result.statute_score:.3f} ✅")
    print(f"  • Interpretation (25%):  {result.interpretation_score:.3f} ✅")
    print(f"  • Synthesis (30%):       {result.synthesis_score:.3f} ❌ MISSING!")
    print(f"  • Practical Effect (20%): {result.practical_effect_score:.3f} ✅")
    
    print(f"\n⚠️ ANALYSIS:")
    print("  Even though 3 out of 4 sections present (75% of weights),")
    print("  missing the SYNTHESIS section (30% weight - the HIGHEST) causes failure.")
    print("  This is intentional: synthesis is the CORE of statutory interpretation!")
    
    print(f"\n📋 How to Fix:")
    print("  Add synthesis language like:")
    print("  • 'While the statute says X, the court held Y'")
    print("  • 'Case law has narrowed the statutory provision to...'")
    print("  • 'The plain text suggests X, but precedent limits this to Y'")
    print("\n")


def main():
    """Run all examples"""
    print("\n🚀 SYNTHESIS QUALITY SCORER EXAMPLES\n")
    
    example_perfect_synthesis()
    example_good_synthesis()
    example_weak_synthesis()
    example_integration_with_validator()
    example_missing_synthesis_penalty()
    
    print("=" * 80)
    print("✅ All examples completed!")
    print("=" * 80)


if __name__ == '__main__':
    main()
