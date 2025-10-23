"""
Extraction pipeline for interpretation links.
Week 2: Core extraction functionality
"""

from .models import (
    InterpretationType,
    Authority,
    ExtractionMethod,
    CaseParagraphInput,
    ExtractionResult,
    InterpretationLink,
)

from .rule_based_extractor import RuleBasedExtractor
from .link_quality_validator import QualityValidator, BatchValidator

# These are optional - only import if files exist
try:
    from .llm_assisted_extractor import LLMAssistedExtractor
except ImportError:
    LLMAssistedExtractor = None

try:
    from .extraction_pipeline_orchestrator import ExtractionPipeline, PipelineConfig
except ImportError:
    ExtractionPipeline = None
    PipelineConfig = None

__all__ = [
    "InterpretationType",
    "Authority",
    "ExtractionMethod",
    "CaseParagraphInput",
    "ExtractionResult",
    "InterpretationLink",
    "RuleBasedExtractor",
    "LLMAssistedExtractor",
    "QualityValidator",
    "BatchValidator",
    "ExtractionPipeline",
    "PipelineConfig",
]
