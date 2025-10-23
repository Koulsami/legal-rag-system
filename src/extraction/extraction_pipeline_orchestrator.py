"""
Interpretation Links Extraction Pipeline Orchestrator

Coordinates rule-based, LLM-assisted, and quality validation.
Week 2: Extraction Pipeline - Part 5/5
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from src.extraction.models import (
    CaseParagraph,
    ExtractionResult,
    InterpretationLink,
)
from rule_based_extractor import RuleBasedExtractor
from llm_assisted_extractor import LLMAssistedExtractor
from link_quality_validator import BatchValidator, QualityValidator


# ============================================================================
# PIPELINE CONFIGURATION
# ============================================================================

class PipelineConfig:
    """Configuration for extraction pipeline"""
    
    def __init__(
        self,
        # Extraction methods to use
        use_rule_based: bool = True,
        use_llm_assisted: bool = True,
        
        # LLM settings
        openai_api_key: Optional[str] = None,
        llm_model: str = "gpt-4o-mini",
        llm_batch_size: int = 10,
        llm_max_paragraphs: Optional[int] = None,  # For testing
        
        # Quality validation
        quality_threshold: float = 0.8,
        
        # Output paths
        output_dir: str = "./data/extraction_output",
        
        # Logging
        verbose: bool = True,
    ):
        self.use_rule_based = use_rule_based
        self.use_llm_assisted = use_llm_assisted
        self.openai_api_key = openai_api_key
        self.llm_model = llm_model
        self.llm_batch_size = llm_batch_size
        self.llm_max_paragraphs = llm_max_paragraphs
        self.quality_threshold = quality_threshold
        self.output_dir = output_dir
        self.verbose = verbose
        
        # Ensure output directory exists
        Path(output_dir).mkdir(parents=True, exist_ok=True)


# ============================================================================
# MAIN PIPELINE ORCHESTRATOR
# ============================================================================

class ExtractionPipeline:
    """
    Orchestrates complete interpretation links extraction
    
    Pipeline Steps:
    1. Load case paragraphs from corpus
    2. Run rule-based extraction
    3. Run LLM-assisted extraction (if enabled)
    4. Merge and deduplicate links
    5. Quality validation
    6. Export results
    """
    
    def __init__(self, config: PipelineConfig):
        """Initialize pipeline with configuration"""
        self.config = config
        
        # Initialize extractors
        self.rule_extractor = RuleBasedExtractor() if config.use_rule_based else None
        self.llm_extractor = (
            LLMAssistedExtractor(
                api_key=config.openai_api_key,
                model=config.llm_model
            )
            if config.use_llm_assisted and config.openai_api_key
            else None
        )
        
        # Initialize validator
        self.validator = BatchValidator(
            QualityValidator({"min_score": config.quality_threshold})
        )
        
        # Results storage
        self.results: Dict[str, ExtractionResult] = {}
        self.all_links: List[InterpretationLink] = []
        self.validated_links: List[InterpretationLink] = []
    
    async def run(
        self,
        case_paragraphs: List[CaseParagraph]
    ) -> Dict:
        """
        Run complete extraction pipeline
        
        Returns:
            Pipeline results dictionary
        """
        start_time = datetime.now()
        
        if self.config.verbose:
            print("\n" + "=" * 70)
            print("INTERPRETATION LINKS EXTRACTION PIPELINE")
            print("=" * 70)
            print(f"Input: {len(case_paragraphs)} case paragraphs")
            print(f"Methods: {'Rule-based ' if self.config.use_rule_based else ''}"
                  f"{'LLM-assisted' if self.config.use_llm_assisted else ''}")
            print("=" * 70 + "\n")
        
        # Step 1: Rule-based extraction
        if self.rule_extractor:
            if self.config.verbose:
                print("Step 1: Rule-Based Extraction")
                print("-" * 70)
            
            rule_result = self.rule_extractor.extract(
                case_paragraphs,
                verbose=self.config.verbose
            )
            self.results["rule_based"] = rule_result
            
            if self.config.verbose:
                print(f"\n{rule_result.summary()}\n")
        
        # Step 2: LLM-assisted extraction
        if self.llm_extractor:
            if self.config.verbose:
                print("Step 2: LLM-Assisted Extraction")
                print("-" * 70)
            
            llm_result = await self.llm_extractor.extract(
                case_paragraphs,
                batch_size=self.config.llm_batch_size,
                max_paragraphs=self.config.llm_max_paragraphs,
                verbose=self.config.verbose
            )
            self.results["llm_assisted"] = llm_result
            
            if self.config.verbose:
                print(f"\n{llm_result.summary()}\n")
        
        # Step 3: Merge links
        if self.config.verbose:
            print("Step 3: Merging Links")
            print("-" * 70)
        
        self.all_links = self._merge_links()
        
        if self.config.verbose:
            print(f"Total unique links: {len(self.all_links)}\n")
        
        # Step 4: Quality validation
        if self.config.verbose:
            print("Step 4: Quality Validation")
            print("-" * 70)
        
        validation_stats = self.validator.validate_and_report(
            self.all_links,
            verbose=self.config.verbose
        )
        self.validated_links = validation_stats["passed_links"]
        
        # Step 5: Export results
        if self.config.verbose:
            print("\nStep 5: Exporting Results")
            print("-" * 70)
        
        export_paths = self._export_results(validation_stats)
        
        if self.config.verbose:
            for key, path in export_paths.items():
                print(f"  {key}: {path}")
        
        # Generate summary
        duration = (datetime.now() - start_time).total_seconds()
        summary = self._generate_summary(validation_stats, duration)
        
        if self.config.verbose:
            print("\n" + "=" * 70)
            print("PIPELINE COMPLETE")
            print("=" * 70)
            print(summary)
            print("=" * 70 + "\n")
        
        return {
            "summary": summary,
            "extraction_results": self.results,
            "all_links": self.all_links,
            "validated_links": self.validated_links,
            "validation_stats": validation_stats,
            "export_paths": export_paths,
        }
    
    def _merge_links(self) -> List[InterpretationLink]:
        """
        Merge links from different extraction methods
        
        Deduplication strategy:
        - Same (statute_id, case_id) = duplicate
        - Keep highest confidence version
        """
        # Collect all links
        all_links = []
        for result in self.results.values():
            all_links.extend(result.links)
        
        # Deduplicate by (statute_id, case_id)
        link_map: Dict[tuple, InterpretationLink] = {}
        
        for link in all_links:
            key = (link.statute_id, link.case_id)
            
            if key not in link_map:
                link_map[key] = link
            else:
                # Keep higher confidence version
                if link.confidence > link_map[key].confidence:
                    link_map[key] = link
        
        return list(link_map.values())
    
    def _export_results(self, validation_stats: Dict) -> Dict[str, str]:
        """Export results to files"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Export all links (before validation)
        all_path = Path(self.config.output_dir) / f"links_all_{timestamp}.json"
        self._save_links_json(self.all_links, all_path)
        
        # Export validated links (passing quality)
        validated_path = Path(self.config.output_dir) / f"links_validated_{timestamp}.json"
        self._save_links_json(self.validated_links, validated_path)
        
        # Export failed links for review
        failed_path = Path(self.config.output_dir) / f"links_failed_{timestamp}.json"
        self.validator.export_failed_for_review(
            validation_stats["failed_scores"],
            str(failed_path)
        )
        
        # Export summary statistics
        stats_path = Path(self.config.output_dir) / f"stats_{timestamp}.json"
        self._save_statistics(validation_stats, stats_path)
        
        return {
            "all_links": str(all_path),
            "validated_links": str(validated_path),
            "failed_links": str(failed_path),
            "statistics": str(stats_path),
        }
    
    def _save_links_json(self, links: List[InterpretationLink], path: Path):
        """Save links to JSON file"""
        data = {
            "count": len(links),
            "timestamp": datetime.now().isoformat(),
            "links": [link.to_dict() for link in links]
        }
        
        with open(path, 'w') as f:
            json.dump(data, f, indent=2)
    
    def _save_statistics(self, validation_stats: Dict, path: Path):
        """Save pipeline statistics"""
        stats = {
            "timestamp": datetime.now().isoformat(),
            "extraction_methods": list(self.results.keys()),
            "total_links_extracted": len(self.all_links),
            "links_validated": validation_stats["passed"],
            "links_failed": validation_stats["failed"],
            "pass_rate": validation_stats["pass_rate"],
            "avg_confidence": validation_stats["avg_confidence"],
            "avg_score": validation_stats["avg_score"],
        }
        
        # Add per-method statistics
        for method_name, result in self.results.items():
            stats[f"{method_name}_links"] = len(result.links)
            stats[f"{method_name}_cases"] = result.total_cases_processed
            stats[f"{method_name}_paragraphs"] = result.total_paragraphs_scanned
            stats[f"{method_name}_duration"] = result.duration_seconds
        
        with open(path, 'w') as f:
            json.dump(stats, f, indent=2)
    
    def _generate_summary(self, validation_stats: Dict, duration: float) -> str:
        """Generate human-readable summary"""
        return f"""
Extraction Summary:
  Total Links Extracted: {len(self.all_links)}
  Links Validated: {validation_stats['passed']} ({validation_stats['pass_rate']:.1%})
  Links Failed: {validation_stats['failed']}
  Average Confidence: {validation_stats['avg_confidence']:.2f}
  Average Quality Score: {validation_stats['avg_score']:.2f}

Per-Method Results:
{self._format_method_results()}

Pipeline Duration: {duration:.1f}s
        """.strip()
    
    def _format_method_results(self) -> str:
        """Format per-method results"""
        lines = []
        for method_name, result in self.results.items():
            lines.append(f"  {method_name.upper()}:")
            lines.append(f"    Links: {len(result.links)}")
            lines.append(f"    Cases: {result.total_cases_processed}")
            lines.append(f"    Avg Confidence: {result.avg_confidence:.2f}")
            lines.append(f"    Duration: {result.duration_seconds:.1f}s")
        return "\n".join(lines)


# ============================================================================
# CONVENIENCE FUNCTION
# ============================================================================

async def run_extraction_pipeline(
    case_paragraphs: List[CaseParagraph],
    config: Optional[PipelineConfig] = None
) -> Dict:
    """
    Convenience function to run extraction pipeline
    
    Args:
        case_paragraphs: List of case paragraphs
        config: Pipeline configuration (uses defaults if None)
        
    Returns:
        Pipeline results dictionary
    """
    if config is None:
        config = PipelineConfig()
    
    pipeline = ExtractionPipeline(config)
    return await pipeline.run(case_paragraphs)


# ============================================================================
# USAGE EXAMPLE
# ============================================================================

async def main():
    """Example usage of full pipeline"""
    import os
    from src.extraction.models import CaseMetadata, CaseParagraph
    
    # Create sample case paragraphs
    sample_paragraphs = [
        CaseParagraph(
            para_no=158,
            text="""
            The Court held that Section 2 of the Misrepresentation Act applies only 
            where there exists a fiduciary relationship or special knowledge. The 
            scope of the duty to disclose is therefore narrowly construed and does 
            not extend to arm's length commercial transactions.
            """,
            case_metadata=CaseMetadata(
                doc_id="sg_case_2013_sgca_36",
                case_name="Wee Chiaw Sek Anna v Ng Li-Ann Genevieve",
                citation="[2013] SGCA 36",
                court="SGCA",
                year=2013
            )
        ),
        CaseParagraph(
            para_no=45,
            text="""
            In determining whether a duty to disclose arises, we must consider the 
            legislative intent behind Section 2. The provision was enacted to protect 
            vulnerable parties in relationships of trust. Accordingly, we adopt a 
            purposive interpretation and hold that the duty extends to situations 
            where one party possesses material information that the other could not 
            reasonably obtain.
            """,
            case_metadata=CaseMetadata(
                doc_id="sg_case_2015_sgca_12",
                case_name="Example Case v Test Case",
                citation="[2015] SGCA 12",
                court="SGCA",
                year=2015
            )
        ),
    ]
    
    # Configure pipeline
    config = PipelineConfig(
        use_rule_based=True,
        use_llm_assisted=True,
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        llm_max_paragraphs=2,  # Limit for testing
        verbose=True,
    )
    
    # Run pipeline
    results = await run_extraction_pipeline(sample_paragraphs, config)
    
    print(f"\n✓ Pipeline complete!")
    print(f"✓ Validated links: {len(results['validated_links'])}")
    print(f"✓ Results exported to: {config.output_dir}")


if __name__ == "__main__":
    asyncio.run(main())
