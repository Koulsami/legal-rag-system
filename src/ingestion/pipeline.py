"""
Main ingestion pipeline orchestrator.

Coordinates the full ingestion workflow:
1. Fetch documents from source
2. Parse documents
3. Load into database
4. Validate integrity
"""

import logging
from typing import Optional, List
from datetime import datetime

from .interfaces import SourceAdapter, DocumentParser, DatabaseLoader, IngestionPipeline
from .models import SourceDocument, ParsedDocument, IngestionResult
from .parsers.statute_parser import StatuteParser
from .parsers.case_parser import CaseParser


logger = logging.getLogger(__name__)


class StandardIngestionPipeline(IngestionPipeline):
    """
    Standard ingestion pipeline implementation.
    
    Flow:
    Source → Parser → Loader → Validation
    """
    
    def __init__(
        self,
        source_adapter: SourceAdapter,
        statute_parser: Optional[StatuteParser] = None,
        case_parser: Optional[CaseParser] = None,
        loader: Optional[DatabaseLoader] = None,
        batch_size: int = 100
    ):
        """
        Initialize pipeline.
        
        Args:
            source_adapter: Source adapter for fetching documents
            statute_parser: Parser for statutes (uses default if None)
            case_parser: Parser for cases (uses default if None)
            loader: Database loader (required)
            batch_size: Documents per batch
        """
        self.source_adapter = source_adapter
        self.statute_parser = statute_parser or StatuteParser()
        self.case_parser = case_parser
        self.rules_parser = rules_parser or CaseParser()
        self.loader = loader
        self.batch_size = batch_size
        
        if not self.loader:
            raise ValueError("Database loader is required")
    
    def run(self) -> IngestionResult:
        """
        Run the complete ingestion pipeline.
        
        Returns:
            IngestionResult with overall statistics
        """
        logger.info("=" * 80)
        logger.info("STARTING INGESTION PIPELINE")
        logger.info("=" * 80)
        
        # Validate pipeline
        is_valid, error = self.validate_pipeline()
        if not is_valid:
            raise ValueError(f"Pipeline validation failed: {error}")
        
        start_time = datetime.now()
        
        # Overall result
        overall_result = IngestionResult(
            source_file=self.source_adapter.get_source_name(),
            status="success",
            start_time=start_time
        )
        
        try:
            # Fetch and parse documents
            all_parsed_docs = []
            
            logger.info(f"Fetching documents from {self.source_adapter.get_source_name()}...")
            
            for source_doc in self.source_adapter.fetch_documents():
                try:
                    # Select appropriate parser
                    parser = self._select_parser(source_doc)
                    
                    if not parser:
                        overall_result.add_skip(
                            source_doc.filepath,
                            f"No parser for {source_doc.source_type}"
                        )
                        continue
                    
                    # Parse document
                    logger.info(f"Parsing {source_doc.filepath}...")
                    parsed_docs = parser.parse(source_doc)
                    
                    # Validate each parsed document
                    for doc in parsed_docs:
                        is_valid, error = parser.validate_document(doc)
                        if is_valid:
                            all_parsed_docs.append(doc)
                        else:
                            overall_result.add_skip(doc.id, f"validation failed: {error}")
                    
                    logger.info(f"  ✓ Parsed {len(parsed_docs)} documents from {source_doc.filepath}")
                    
                except Exception as e:
                    error_msg = f"Failed to parse {source_doc.filepath}: {str(e)}"
                    logger.error(error_msg)
                    overall_result.add_error(error_msg)
            
            # Update total count
            overall_result.total_documents = len(all_parsed_docs)
            
            logger.info(f"\nParsed {len(all_parsed_docs)} valid documents")
            logger.info(f"Loading into database in batches of {self.batch_size}...")
            
            # Load into database
            if all_parsed_docs:
                all_parsed_docs = sorted(all_parsed_docs, key=lambda d: d.level) 
                load_result = self.loader.load_documents(
                    all_parsed_docs,
                    batch_size=self.batch_size
                )
                
                # Merge results
                overall_result.inserted = load_result.inserted
                overall_result.skipped += load_result.skipped
                overall_result.errors += load_result.errors
                overall_result.error_messages.extend(load_result.error_messages)
                overall_result.inserted_ids = load_result.inserted_ids
                overall_result.skipped_ids.extend(load_result.skipped_ids)
            
            # Finalize
            overall_result.finalize()
            
            # Determine final status
            if overall_result.errors > 0:
                overall_result.status = "partial" if overall_result.inserted > 0 else "failed"
            else:
                overall_result.status = "success"
            
            # Log summary
            logger.info("\n" + "=" * 80)
            logger.info("INGESTION COMPLETE")
            logger.info("=" * 80)
            logger.info(overall_result.summary())
            logger.info(f"  Inserted IDs: {len(overall_result.inserted_ids)}")
            logger.info(f"  Skipped IDs: {len(overall_result.skipped_ids)}")
            logger.info(f"  Error count: {overall_result.errors}")
            
            return overall_result
            
        except Exception as e:
            overall_result.status = "failed"
            overall_result.add_error(f"Pipeline failed: {str(e)}")
            overall_result.finalize()
            logger.error(f"Pipeline failed: {str(e)}", exc_info=True)
            raise
    
    def _select_parser(self, source_doc: SourceDocument) -> Optional[DocumentParser]:
        """
        Select appropriate parser for document.
        
        Args:
            source_doc: Source document
            
        Returns:
            Parser instance or None
        """
        if source_doc.source_type == 'statute':
            return self.statute_parser
        elif source_doc.source_type == 'case':
            return self.case_parser
        else:
            return None
    
    def validate_pipeline(self) -> tuple[bool, Optional[str]]:
        """
        Validate pipeline configuration.
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not self.source_adapter:
            return False, "Source adapter is required"
        
        if not self.loader:
            return False, "Database loader is required"
        
        if not self.source_adapter.validate_source():
            return False, f"Source '{self.source_adapter.get_source_name()}' is not accessible"
        
        return True, None


# ============================================================================
# Helper Functions for Running Pipeline
# ============================================================================

def run_ingestion(
    source_adapter: SourceAdapter,
    loader: DatabaseLoader,
    statute_parser: Optional[StatuteParser] = None,
    case_parser: Optional[CaseParser] = None,
    batch_size: int = 100
) -> IngestionResult:
    """
    Convenience function to run ingestion pipeline.
    
    Args:
        source_adapter: Source adapter
        loader: Database loader
        statute_parser: Optional statute parser
        case_parser: Optional case parser
        batch_size: Batch size
        
    Returns:
        IngestionResult
    """
    pipeline = StandardIngestionPipeline(
        source_adapter=source_adapter,
        statute_parser=statute_parser,
        case_parser=case_parser,
        loader=loader,
        batch_size=batch_size
    )
    
    return pipeline.run()


def ingest_from_filesystem(
    loader: DatabaseLoader,
    statute_dir: str = 'data/statutes/raw',
    case_dir: str = 'data/cases/raw',
    batch_size: int = 100
) -> IngestionResult:
    """
    Convenience function to ingest from filesystem.
    
    Args:
        loader: Database loader
        statute_dir: Directory containing statutes
        case_dir: Directory containing cases
        batch_size: Batch size
        
    Returns:
        IngestionResult
    """
    from .sources.sample_adapter import FileAdapter
    
    adapter = FileAdapter(config={
        'statute_dir': statute_dir,
        'case_dir': case_dir
    })
    
    return run_ingestion(
        source_adapter=adapter,
        loader=loader,
        batch_size=batch_size
    )


def ingest_sample_data(
    loader: DatabaseLoader,
    include_statutes: bool = True,
    include_cases: bool = True,
    batch_size: int = 100
) -> IngestionResult:
    """
    Convenience function to ingest sample data.
    
    Args:
        loader: Database loader
        include_statutes: Include sample statutes
        include_cases: Include sample cases
        batch_size: Batch size
        
    Returns:
        IngestionResult
    """
    from .sources.sample_adapter import SampleAdapter
    
    adapter = SampleAdapter(config={
        'include_statutes': include_statutes,
        'include_cases': include_cases
    })
    
    return run_ingestion(
        source_adapter=adapter,
        loader=loader,
        batch_size=batch_size
    )
