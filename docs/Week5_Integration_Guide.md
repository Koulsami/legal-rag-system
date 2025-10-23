# Week 5 Integration Guide
## Combining Citation Validation + Synthesis Quality Scoring

This guide shows how to use the Week 5 validation pipeline in your Legal RAG system.

---

## 🏗️ Architecture Overview

```
User Query
    ↓
Retrieval System
    ↓
Generation (LLM)
    ↓
┌─────────────────────────────────┐
│  WEEK 5 VALIDATION PIPELINE     │
│                                 │
│  ┌──────────────────────────┐  │
│  │ 1. Synthesis Scorer      │  │  Score: 0-1
│  │    - Statute (25%)       │  │  Threshold: ≥ 0.7
│  │    - Interpretation (25%)│  │
│  │    - Synthesis (30%) ⭐  │  │
│  │    - Practical (20%)     │  │
│  └──────────────────────────┘  │
│            ↓                    │
│  ┌──────────────────────────┐  │
│  │ 2. Citation Validator    │  │  6 Stages
│  │    - Existence           │  │  Threshold: ≥ 0.75
│  │    - Text Alignment      │  │
│  │    - Propositional       │  │
│  │    - Jurisdiction        │  │
│  │    - Temporal            │  │
│  │    - Interpretation Link │  │
│  └──────────────────────────┘  │
│            ↓                    │
│  ┌──────────────────────────┐  │
│  │ 3. Routing Decision      │  │
│  │    Pass → User           │  │
│  │    Fail → Review Queue   │  │
│  │    Critical → Auto-Reject│  │
│  └──────────────────────────┘  │
└─────────────────────────────────┘
    ↓
User / Review Queue
```

---

## 🚀 Quick Start

### Basic Usage

```python
from validation.synthesis_quality_scorer import SynthesisQualityScorer
from validation.enhanced_citation_validator import EnhancedCitationValidator
from config.week5_config import get_week5_config

# Initialize
config = get_week5_config()
synthesis_scorer = SynthesisQualityScorer()
citation_validator = EnhancedCitationValidator()

# Your RAG system generates an answer
answer = generate_answer(query, context)

# Step 1: Score synthesis quality
synthesis_result = synthesis_scorer.score_answer(answer)

if synthesis_result.passed:
    # Step 2: Validate citations (only if synthesis passed)
    citation_result = citation_validator.validate_answer(answer, context)
    
    if citation_result.passed:
        # Both passed → send to user
        return {"answer": answer, "validated": True}
    else:
        # Failed citation → review queue
        return {
            "answer": answer,
            "status": "needs_review",
            "reason": "citation_validation_failed",
            "details": citation_result.to_dict()
        }
else:
    # Failed synthesis → review queue
    return {
        "answer": answer,
        "status": "needs_review",
        "reason": "synthesis_quality_failed",
        "details": synthesis_result.to_dict()
    }
```

---

## 📊 Scoring Details

### Synthesis Quality (Threshold: 0.7)

| Section | Weight | What It Checks |
|---------|--------|----------------|
| **Statute** | 25% | Has statute citations? Quoted text? |
| **Interpretation** | 25% | Has case citations? Paragraph refs? |
| **Synthesis** | **30%** ⭐ | Explains relationship? Uses synthesis language? |
| **Practical Effect** | 20% | Has practical summary? Final takeaway? |

**Pass Example:**
```
Synthesis Score: 0.85 ✅
  • Statute: 0.90 (Clear citation + quoted text)
  • Interpretation: 0.85 (Case citation + ¶ ref + marker)
  • Synthesis: 0.80 (Good relationship language)
  • Practical: 0.90 (Strong practical summary)
```

**Fail Example:**
```
Synthesis Score: 0.52 ❌
  • Statute: 0.70 (Citation but no quote)
  • Interpretation: 0.60 (Case citation only)
  • Synthesis: 0.30 ❌ (No relationship language!)
  • Practical: 0.65 (Weak summary)
```

---

### Citation Validation (Threshold: 0.75)

| Stage | Weight | What It Checks |
|-------|--------|----------------|
| Existence | 20% | Citation exists in corpus? |
| Text Alignment | 15% | Quoted text matches source? |
| Propositional Support | 20% | Citation supports claim? |
| Jurisdiction | 15% | Court authority level? |
| Temporal Validity | 10% | Still good law? Not overruled? |
| **Interpretation Link** | **20%** | Verified in DB? |

---

## 🎯 Routing Logic

### Decision Tree

```python
def route_answer(synthesis_score, citation_score):
    """
    Routing decision based on scores.
    
    Returns: 'pass', 'review', or 'auto_reject'
    """
    # Auto-reject: Terrible scores
    if synthesis_score < 0.3 or citation_score < 0.4:
        return 'auto_reject'
    
    # Pass: Both passed thresholds
    if synthesis_score >= 0.7 and citation_score >= 0.75:
        return 'pass'
    
    # Review: Failed one or both
    return 'review'
```

### Priority Levels for Review Queue

| Priority | Criteria | Action |
|----------|----------|--------|
| **Critical** | Failed both synthesis AND citation | Immediate review |
| **High** | Failed one major check | Review within 24h |
| **Medium** | Borderline on one metric | Review within week |
| **Low** | Minor issues only | Review when available |

---

## 💻 Complete Integration Example

```python
"""
complete_validation_pipeline.py

Full Week 5 validation pipeline.
"""

from typing import Dict, Optional
from dataclasses import dataclass
from validation.synthesis_quality_scorer import SynthesisQualityScorer
from validation.enhanced_citation_validator import EnhancedCitationValidator
from config.week5_config import Week5Config, get_week5_config


@dataclass
class ValidationResult:
    """Complete validation result"""
    answer: str
    passed: bool
    synthesis_score: float
    citation_score: float
    route: str  # 'pass', 'review', 'auto_reject'
    priority: Optional[str]
    feedback: list
    details: dict


class Week5ValidationPipeline:
    """
    Complete Week 5 validation pipeline.
    
    Combines:
    1. Synthesis quality scoring
    2. Citation validation
    3. Routing decision
    """
    
    def __init__(self, config: Optional[Week5Config] = None):
        """Initialize pipeline with config"""
        self.config = config or get_week5_config()
        self.synthesis_scorer = SynthesisQualityScorer()
        self.citation_validator = EnhancedCitationValidator()
    
    def validate(
        self,
        answer: str,
        query: Optional[str] = None,
        context: Optional[Dict] = None
    ) -> ValidationResult:
        """
        Run complete validation pipeline.
        
        Args:
            answer: Generated answer to validate
            query: Original query (optional)
            context: Retrieved context (optional)
            
        Returns:
            ValidationResult with all scores and routing
        """
        # Step 1: Score synthesis quality
        synthesis_result = self.synthesis_scorer.score_answer(
            answer, query, context
        )
        
        # Step 2: Validate citations
        citation_result = self.citation_validator.validate_answer(
            answer, context
        )
        
        # Step 3: Determine routing
        route = self._determine_route(
            synthesis_result.overall_score,
            citation_result.overall_score
        )
        
        # Step 4: Determine priority if going to review
        priority = None
        if route == 'review':
            priority = self.config.review_queue.determine_priority(
                synthesis_result.overall_score,
                citation_result.overall_score
            )
        
        # Step 5: Combine feedback
        feedback = self._combine_feedback(
            synthesis_result,
            citation_result,
            route
        )
        
        return ValidationResult(
            answer=answer,
            passed=(route == 'pass'),
            synthesis_score=synthesis_result.overall_score,
            citation_score=citation_result.overall_score,
            route=route,
            priority=priority,
            feedback=feedback,
            details={
                'synthesis': synthesis_result.to_dict(),
                'citation': citation_result.to_dict() if hasattr(citation_result, 'to_dict') else {}
            }
        )
    
    def _determine_route(
        self,
        synthesis_score: float,
        citation_score: float
    ) -> str:
        """Determine routing based on scores"""
        
        # Auto-reject: Terrible scores
        if (synthesis_score < self.config.review_queue.auto_reject_synthesis_threshold or
            citation_score < self.config.review_queue.auto_reject_citation_threshold):
            return 'auto_reject'
        
        # Pass: Both passed thresholds
        if (synthesis_score >= self.config.synthesis.pass_threshold and
            citation_score >= self.config.citation.overall_pass_threshold):
            return 'pass'
        
        # Review: Failed one or both
        return 'review'
    
    def _combine_feedback(
        self,
        synthesis_result,
        citation_result,
        route: str
    ) -> list:
        """Combine feedback from both validators"""
        feedback = []
        
        if route == 'auto_reject':
            feedback.append("❌ Answer quality too low - auto-rejected")
        
        if route == 'review':
            if synthesis_result.overall_score < self.config.synthesis.pass_threshold:
                feedback.append(f"⚠️ Synthesis quality: {synthesis_result.overall_score:.2f} < {self.config.synthesis.pass_threshold}")
                feedback.extend(synthesis_result.feedback)
            
            if citation_result.overall_score < self.config.citation.overall_pass_threshold:
                feedback.append(f"⚠️ Citation quality: {citation_result.overall_score:.2f} < {self.config.citation.overall_pass_threshold}")
        
        if route == 'pass':
            feedback.append("✅ Answer passed all validation checks")
        
        return feedback


# Example usage
if __name__ == '__main__':
    # Initialize pipeline
    pipeline = Week5ValidationPipeline()
    
    # Test answer
    test_answer = """
    **Statute:** Defamation Act, Section 7 provides "truth and public benefit" defense.
    
    **Interpretation:** Court held in Lim v SPH [2015] SGCA 33, ¶45 that public benefit 
    requires demonstrable social utility. [INTERPRETS STATUTE: Defamation Act, Section 7]
    
    **Synthesis:** While the statute appears broad, case law has narrowed this by 
    requiring proof of positive public benefit beyond mere public interest.
    
    **Practical Effect:** In practice, defendants must demonstrate that publishing 
    the information materially benefited society.
    """
    
    # Validate
    result = pipeline.validate(test_answer)
    
    # Print results
    print(f"\n{'='*60}")
    print(f"VALIDATION RESULT")
    print(f"{'='*60}")
    print(f"Route: {result.route.upper()}")
    print(f"Synthesis Score: {result.synthesis_score:.3f}")
    print(f"Citation Score: {result.citation_score:.3f}")
    
    if result.priority:
        print(f"Review Priority: {result.priority.upper()}")
    
    print(f"\nFeedback:")
    for item in result.feedback:
        print(f"  • {item}")
    
    print(f"\n{'='*60}\n")
```

---

## 🧪 Testing

### Run Unit Tests

```bash
# Test synthesis scorer
pytest tests/validation/test_synthesis_quality_scorer.py -v

# Test citation validator
pytest tests/validation/test_enhanced_citation_validator.py -v

# Test all Week 5
pytest tests/validation/ -v
```

### Run Examples

```bash
# Synthesis scoring examples
python examples/synthesis_scoring_examples.py

# Integration examples
python validation/complete_validation_pipeline.py
```

---

## 📈 Metrics to Track

### Success Metrics (from Project Requirements)

| Metric | Target | Current |
|--------|--------|---------|
| Synthesis Quality | ≥ 0.8 → **0.7** | TBD |
| Citation Precision | ≥ 95% | TBD |
| Hallucination Rate | ≤ 5% | TBD |
| Interpretation Coverage | ≥ 80% | **41/41 links** |

### Monitoring Dashboard

```python
{
  "daily_stats": {
    "total_answers": 1247,
    "passed": 891,           # 71%
    "review_queue": 312,     # 25%
    "auto_rejected": 44,     # 4%
    
    "avg_synthesis_score": 0.76,
    "avg_citation_score": 0.81,
    
    "review_breakdown": {
      "critical": 12,
      "high": 89,
      "medium": 156,
      "low": 55
    }
  }
}
```

---

## 🚨 Common Issues

### Issue 1: Low Synthesis Scores

**Problem:** Most answers scoring < 0.7

**Solutions:**
- Check if generation prompts include 4-step structure
- Add few-shot examples to prompts
- Verify [INTERPRETS STATUTE] markers in context
- Review synthesis language in training data

### Issue 2: High Review Queue Volume

**Problem:** > 30% of answers going to review

**Solutions:**
- Adjust thresholds (0.7 → 0.65 for synthesis)
- Improve generation prompts
- Add more interpretation links to database
- Fine-tune LLM on high-quality examples

### Issue 3: False Positives (Good answers marked as bad)

**Problem:** Legitimate answers failing validation

**Solutions:**
- Review pattern detection (may be too strict)
- Add more synthesis phrase patterns
- Check for alternative citation formats
- Manual review of false positives to refine patterns

---

## 🎯 Next Steps (Week 5 Day 3+)

1. **Day 3:** Hallucination Detection
   - Extract all cross-document claims
   - Verify against interpretation_links DB
   - Flag unverified statute-case claims

2. **Day 4:** Integration Testing
   - End-to-end pipeline tests
   - Performance benchmarking
   - Error handling

3. **Day 5:** Dashboard & Reporting
   - Review queue interface
   - Metrics visualization
   - Feedback collection

---

## 📚 References

- **Patent:** Claims 5 (Synthesis Quality Evaluation)
- **Config:** `config/week5_config.py`
- **Day 1:** `validation/enhanced_citation_validator.py`
- **Day 2:** `validation/synthesis_quality_scorer.py`
- **Requirements:** `Project_Requirements_v3_Statutory_Interpretation.md`

---

**Last Updated:** Week 5 Day 2  
**Status:** ✅ Ready for Integration
