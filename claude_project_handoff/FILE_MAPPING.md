# File Mapping: Design → Implementation

## Old Design Examples vs New Real Code

| Design Example (06_Code_Examples/)        | Real Implementation              | Status |
|-------------------------------------------|----------------------------------|--------|
| `interpretation_validator.py`             | `validation/enhanced_citation_validator.py` | ✅ Implemented |
| `interpretation_aware_retrieval.py`       | `src/retrieval/hybrid_retriever.py` | ✅ Implemented |
| `statutory_interpretation_prompts.py`     | `src/generation/rag_generator.py` | ✅ Implemented |
| N/A                                       | `validation/integrated_validation_pipeline.py` | ✅ NEW - Main validation |
| N/A                                       | `validation/synthesis_quality_scorer.py` | ✅ NEW - Quality scoring |

## Example Data vs Real Results

| Design Examples (07_Examples/)            | Real Test Results                | Status |
|-------------------------------------------|----------------------------------|--------|
| `Example_Queries_With_Expected_Results.json` | `evaluation/queries/statutory_interpretation_50.json` | ✅ Real queries |
| `Example_Good_vs_Bad_Answers.md`          | `evaluation/reports/latest.json` | ✅ Actual results |

## When in Doubt

**ALWAYS prioritize:**
1. Files in `validation/`, `evaluation/`, `src/` (real code)
2. Files with "latest" in name (current results)
3. Files with `.py` extension in new folders (actual implementation)

**OLD = Design mockups for planning**
**NEW = Working, tested, production code**
