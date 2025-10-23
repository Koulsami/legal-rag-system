"""
Interpretation Link Quality Validator

Validates extracted links to ensure high quality before database insertion.
Targets: 80%+ links pass quality threshold

Week 2: Extraction Pipeline - Part 4/5
"""

import re
from typing import Dict, List

from src.extraction.models import (
    InterpretationLink,
    LinkQualityScore,
    ValidationCheck,
)


# ============================================================================
# QUALITY THRESHOLDS
# ============================================================================

QUALITY_THRESHOLDS = {
    "min_score": 0.8,           # Overall quality score
    "min_confidence": 0.6,      # Extraction confidence
    "min_text_length": 50,      # Minimum case text length
    "min_holding_length": 20,   # Minimum holding length
}


# ============================================================================
# VALIDATION CHECKS
# ============================================================================

class QualityValidator:
    """
    Validates interpretation link quality
    
    Checks:
    1. Statute actually mentioned in case paragraph
    2. Case text sufficient length (not just citation)
    3. Contains interpretation keywords
    4. Authority appropriate for court level
    5. Confidence above threshold
    6. Holding is meaningful (not empty/truncated)
    7. No obvious false positives
    """
    
    # Interpretation keywords to verify
    INTERPRETATION_KEYWORDS = [
        'held', 'construed', 'interpreted', 'means', 'applies',
        'requires', 'narrow', 'broad', 'purposive', 'clarify',
        'scope', 'extent', 'meaning', 'purpose'
    ]
    
    # Red flag patterns (likely false positives)
    RED_FLAGS = [
        r'^[\[\d\]]+$',  # Just citation markers
        r'^see\s+also',   # Cross-reference only
        r'^cf\.',         # Comparison reference
    ]
    
    def __init__(self, thresholds: Dict[str, float] = None):
        """
        Initialize validator
        
        Args:
            thresholds: Custom quality thresholds
        """
        self.thresholds = thresholds or QUALITY_THRESHOLDS
    
    def validate(self, link: InterpretationLink) -> LinkQualityScore:
        """
        Validate a single interpretation link
        
        Returns:
            LinkQualityScore with pass/fail and detailed checks
        """
        checks: List[ValidationCheck] = []
        
        # Check 1: Statute mentioned in case text
        checks.append(self._check_statute_mentioned(link))
        
        # Check 2: Sufficient text length
        checks.append(self._check_text_length(link))
        
        # Check 3: Contains interpretation keywords
        checks.append(self._check_interpretation_keywords(link))
        
        # Check 4: Authority appropriate for court
        checks.append(self._check_authority_level(link))
        
        # Check 5: Confidence threshold
        checks.append(self._check_confidence(link))
        
        # Check 6: Holding quality
        checks.append(self._check_holding_quality(link))
        
        # Check 7: No red flags
        checks.append(self._check_no_red_flags(link))
        
        # Compute overall score (weighted average)
        weights = [0.20, 0.15, 0.20, 0.10, 0.15, 0.15, 0.05]
        score = sum(
            w * (1.0 if c.passed else 0.0)
            for w, c in zip(weights, checks)
        )
        
        passed = score >= self.thresholds["min_score"]
        
        return LinkQualityScore(
            link=link,
            score=score,
            checks=checks,
            passed=passed
        )
    
    def validate_batch(
        self,
        links: List[InterpretationLink]
    ) -> List[LinkQualityScore]:
        """Validate multiple links"""
        return [self.validate(link) for link in links]
    
    def filter_passing(
        self,
        links: List[InterpretationLink]
    ) -> List[InterpretationLink]:
        """
        Return only links that pass quality validation
        
        Returns:
            Filtered list of high-quality links
        """
        scores = self.validate_batch(links)
        return [s.link for s in scores if s.passed]
    
    # ========================================================================
    # Individual Check Methods
    # ========================================================================
    
    def _check_statute_mentioned(self, link: InterpretationLink) -> ValidationCheck:
        """Check if statute is actually mentioned in case text"""
        case_text_lower = link.case_text.lower()
        
        # Check for statute name or section number
        statute_mentioned = (
            link.statute_name.lower() in case_text_lower or
            f"section {link.statute_section}" in case_text_lower or
            f"s. {link.statute_section}" in case_text_lower or
            f"s {link.statute_section}" in case_text_lower
        )
        
        return ValidationCheck(
            check_name="statute_mentioned",
            passed=statute_mentioned,
            details=f"Statute '{link.statute_name}' s{link.statute_section} found in text"
                   if statute_mentioned else "Statute not found in case text"
        )
    
    def _check_text_length(self, link: InterpretationLink) -> ValidationCheck:
        """Check if case text is sufficient length"""
        min_length = self.thresholds["min_text_length"]
        text_length = len(link.case_text.strip())
        passed = text_length >= min_length
        
        return ValidationCheck(
            check_name="sufficient_length",
            passed=passed,
            details=f"Text length: {text_length} chars (min: {min_length})"
        )
    
    def _check_interpretation_keywords(self, link: InterpretationLink) -> ValidationCheck:
        """Check if text contains interpretation keywords"""
        text_lower = link.case_text.lower()
        
        found_keywords = [
            kw for kw in self.INTERPRETATION_KEYWORDS
            if kw in text_lower
        ]
        
        passed = len(found_keywords) > 0
        
        return ValidationCheck(
            check_name="has_interpretation_keywords",
            passed=passed,
            details=f"Found keywords: {', '.join(found_keywords)}" if found_keywords
                   else "No interpretation keywords found"
        )
    
    def _check_authority_level(self, link: InterpretationLink) -> ValidationCheck:
        """Check if authority is appropriate for court"""
        court = link.court.upper()
        authority = link.authority
        
        # Singapore Court of Appeal should be BINDING (unless obiter/dissent)
        if court in {"SGCA", "CA"}:
            appropriate = authority.value in {"BINDING", "OBITER", "DISSENT"}
        else:
            # Other courts can be any authority
            appropriate = True
        
        return ValidationCheck(
            check_name="authority_appropriate",
            passed=appropriate,
            details=f"{court} with {authority.value} authority is {'appropriate' if appropriate else 'inappropriate'}"
        )
    
    def _check_confidence(self, link: InterpretationLink) -> ValidationCheck:
        """Check if confidence meets threshold"""
        min_conf = self.thresholds["min_confidence"]
        passed = link.confidence >= min_conf
        
        return ValidationCheck(
            check_name="confidence_threshold",
            passed=passed,
            details=f"Confidence: {link.confidence:.2f} (min: {min_conf:.2f})"
        )
    
    def _check_holding_quality(self, link: InterpretationLink) -> ValidationCheck:
        """Check if holding is meaningful"""
        holding = link.holding.strip()
        min_length = self.thresholds["min_holding_length"]
        
        # Check length
        if len(holding) < min_length:
            return ValidationCheck(
                check_name="holding_quality",
                passed=False,
                details=f"Holding too short: {len(holding)} chars (min: {min_length})"
            )
        
        # Check not just truncation marker
        if holding == "...":
            return ValidationCheck(
                check_name="holding_quality",
                passed=False,
                details="Holding is just truncation marker"
            )
        
        # Check contains some legal content
        has_legal_content = any(
            word in holding.lower()
            for word in ['court', 'held', 'section', 'act', 'applies', 'means']
        )
        
        return ValidationCheck(
            check_name="holding_quality",
            passed=has_legal_content,
            details="Holding contains legal content" if has_legal_content
                   else "Holding lacks legal content"
        )
    
    def _check_no_red_flags(self, link: InterpretationLink) -> ValidationCheck:
        """Check for obvious false positive patterns"""
        text = link.case_text.strip()
        
        for pattern in self.RED_FLAGS:
            if re.match(pattern, text, re.IGNORECASE):
                return ValidationCheck(
                    check_name="no_red_flags",
                    passed=False,
                    details=f"Red flag pattern matched: {pattern}"
                )
        
        return ValidationCheck(
            check_name="no_red_flags",
            passed=True,
            details="No red flag patterns detected"
        )


# ============================================================================
# BATCH VALIDATION UTILITIES
# ============================================================================

class BatchValidator:
    """Validate and filter large batches of links"""
    
    def __init__(self, validator: QualityValidator = None):
        """Initialize with validator"""
        self.validator = validator or QualityValidator()
    
    def validate_and_report(
        self,
        links: List[InterpretationLink],
        verbose: bool = True
    ) -> Dict:
        """
        Validate links and generate report
        
        Returns:
            Report dictionary with statistics
        """
        scores = self.validator.validate_batch(links)
        
        passed = [s for s in scores if s.passed]
        failed = [s for s in scores if not s.passed]
        
        # Compute statistics
        stats = {
            "total": len(links),
            "passed": len(passed),
            "failed": len(failed),
            "pass_rate": len(passed) / len(links) if links else 0.0,
            "avg_score": sum(s.score for s in scores) / len(scores) if scores else 0.0,
            "avg_confidence": sum(l.confidence for l in links) / len(links) if links else 0.0,
            "passed_links": [s.link for s in passed],
            "failed_links": [s.link for s in failed],
            "failed_scores": failed,
        }
        
        if verbose:
            self._print_report(stats)
        
        return stats
    
    def _print_report(self, stats: Dict):
        """Print validation report"""
        print("\n" + "=" * 70)
        print("INTERPRETATION LINK QUALITY VALIDATION REPORT")
        print("=" * 70)
        print(f"Total Links: {stats['total']}")
        print(f"Passed: {stats['passed']} ({stats['pass_rate']:.1%})")
        print(f"Failed: {stats['failed']} ({1 - stats['pass_rate']:.1%})")
        print(f"Average Score: {stats['avg_score']:.2f}")
        print(f"Average Confidence: {stats['avg_confidence']:.2f}")
        
        if stats['failed'] > 0 and stats['failed'] <= 10:
            print("\nFailed Links:")
            for score in stats['failed_scores'][:10]:
                print(f"\n  {score.link.statute_id} → {score.link.case_id}")
                print(f"  Score: {score.score:.2f}")
                failed_checks = [c for c in score.checks if not c.passed]
                for check in failed_checks:
                    print(f"    ✗ {check.check_name}: {check.details}")
        
        print("=" * 70 + "\n")
    
    def export_failed_for_review(
        self,
        scores: List[LinkQualityScore],
        output_path: str
    ):
        """Export failed links for manual review"""
        import json
        
        failed = [s for s in scores if not s.passed]
        
        export_data = []
        for score in failed:
            export_data.append({
                "statute_id": score.link.statute_id,
                "case_id": score.link.case_id,
                "score": score.score,
                "failed_checks": [
                    {"check": c.check_name, "details": c.details}
                    for c in score.checks if not c.passed
                ],
                "case_text": score.link.case_text[:200] + "...",
                "holding": score.link.holding,
            })
        
        with open(output_path, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        print(f"Exported {len(failed)} failed links to {output_path}")


# ============================================================================
# USAGE EXAMPLE
# ============================================================================

if __name__ == "__main__":
    from datetime import datetime
    
    # Create sample links
    good_link = InterpretationLink(
        statute_id="sg_statute_misrepresentation_act_s2",
        case_id="sg_case_2013_sgca_36_para_158",
        statute_name="Misrepresentation Act",
        statute_section="2",
        case_text="""
        The Court held that Section 2 of the Misrepresentation Act applies only 
        where there exists a fiduciary relationship or special knowledge. The 
        scope is therefore narrowly construed.
        """,
        case_name="Wee Chiaw Sek Anna v Ng Li-Ann",
        case_citation="[2013] SGCA 36",
        case_para_no=158,
        court="SGCA",
        year=2013,
        interpretation_type=InterpretationType.NARROW,
        authority=Authority.BINDING,
        holding="Section 2 applies only to fiduciary relationships",
        extraction_method=ExtractionMethod.RULE_BASED,
        confidence=0.85,
        boost_factor=2.8,
    )
    
    bad_link = InterpretationLink(
        statute_id="sg_statute_evidence_act_s32",
        case_id="sg_case_2020_sghc_100_para_5",
        statute_name="Evidence Act",
        statute_section="32",
        case_text="[5]",  # Too short
        case_name="Test Case",
        case_citation="[2020] SGHC 100",
        case_para_no=5,
        court="SGHC",
        year=2020,
        interpretation_type=InterpretationType.CLARIFY,
        authority=Authority.PERSUASIVE,
        holding="...",  # Empty holding
        extraction_method=ExtractionMethod.LLM_ASSISTED,
        confidence=0.4,  # Low confidence
        boost_factor=1.5,
    )
    
    # Validate
    validator = QualityValidator()
    batch_validator = BatchValidator(validator)
    
    links = [good_link, bad_link]
    stats = batch_validator.validate_and_report(links, verbose=True)
    
    print(f"\nPassing links: {len(stats['passed_links'])}")
    print(f"Failing links: {len(stats['failed_links'])}")
