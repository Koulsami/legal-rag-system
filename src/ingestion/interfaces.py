"""
Abstract base classes for ingestion pipeline components.

Defines interfaces for:
- Source adapters (fetch documents from sources)
- Document parsers (extract text and metadata)
- Database loaders (insert into documents table)
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Iterator
from pathlib import Path

from .models import SourceDocument, ParsedDocument, IngestionResult, ParserConfig


# ============================================================================
# Source Adapter Interface
# ============================================================================

class SourceAdapter(ABC):
    """Abstract base class for document source adapters"""
    
    def __init__(self, config: Optional[dict] = None):
        self.config = config or {}
    
    @abstractmethod
    def fetch_documents(self) -> Iterator[SourceDocument]:
        """
        Fetch documents from source.
        
        Yields:
            SourceDocument: Raw documents from source
        """
        pass
    
    @abstractmethod
    def validate_source(self) -> bool:
        """
        Validate that source is accessible.
        
        Returns:
            bool: True if source is accessible
        """
        pass
    
    def get_source_name(self) -> str:
        """Get human-readable source name"""
        return self.__class__.__name__


# ============================================================================
# Document Parser Interface
# ============================================================================

class DocumentParser(ABC):
    """Abstract base class for document parsers"""
    
    def __init__(self, config: Optional[ParserConfig] = None):
        self.config = config or ParserConfig()
    
    @abstractmethod
    def parse(self, source_doc: SourceDocument) -> List[ParsedDocument]:
        """
        Parse source document into structured documents.
        
        Args:
            source_doc: Raw source document
            
        Returns:
            List of parsed documents (may be multiple if splitting hierarchically)
        """
        pass
    
    @abstractmethod
    def supports_format(self, format: str) -> bool:
        """
        Check if parser supports a file format.
        
        Args:
            format: File format (pdf, html, txt, etc.)
            
        Returns:
            bool: True if format is supported
        """
        pass
    
    def validate_document(self, doc: ParsedDocument) -> tuple[bool, Optional[str]]:
        """
        Validate parsed document.
        
        Args:
            doc: Parsed document to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check required fields
        if not doc.id:
            return False, "Document ID is required"
        if not doc.full_text or len(doc.full_text.strip()) == 0:
            return False, "Document text cannot be empty"
        if not doc.title:
            return False, "Document title is required"
        
        # Check hierarchy constraints
        if doc.level > 0 and not doc.parent_id:
            return False, f"Level {doc.level} document requires parent_id"
        
        # Check type-specific fields
        if doc.doc_type == "statute":
            if not doc.act_name:
                return False, "Statutes must have act_name"
            if doc.level > 0 and not doc.section_number:
                return False, "Statute sections must have section_number"
        
        elif doc.doc_type == "case":
            if not doc.citation:
                return False, "Cases must have citation"
            if doc.level > 0 and not doc.para_no:
                return False, "Case paragraphs must have para_no"
        
        return True, None


# ============================================================================
# Database Loader Interface
# ============================================================================

class DatabaseLoader(ABC):
    """Abstract base class for database loaders"""
    
    @abstractmethod
    def load_documents(
        self,
        documents: List[ParsedDocument],
        batch_size: int = 100
    ) -> IngestionResult:
        """
        Load documents into database.
        
        Args:
            documents: List of parsed documents
            batch_size: Number of documents per batch
            
        Returns:
            IngestionResult with statistics
        """
        pass
    
    @abstractmethod
    def document_exists(self, doc_id: str) -> bool:
        """
        Check if document already exists in database.
        
        Args:
            doc_id: Document ID
            
        Returns:
            bool: True if document exists
        """
        pass
    
    @abstractmethod
    def get_document_by_hash(self, hash: str) -> Optional[ParsedDocument]:
        """
        Find document by content hash.
        
        Args:
            hash: SHA-256 content hash
            
        Returns:
            ParsedDocument if found, None otherwise
        """
        pass


# ============================================================================
# Pipeline Interface
# ============================================================================

class IngestionPipeline(ABC):
    """Abstract base class for ingestion pipelines"""
    
    def __init__(
        self,
        source_adapter: SourceAdapter,
        parser: DocumentParser,
        loader: DatabaseLoader
    ):
        self.source_adapter = source_adapter
        self.parser = parser
        self.loader = loader
    
    @abstractmethod
    def run(self) -> IngestionResult:
        """
        Run the complete ingestion pipeline.
        
        Returns:
            IngestionResult with overall statistics
        """
        pass
    
    def validate_pipeline(self) -> tuple[bool, Optional[str]]:
        """
        Validate that pipeline components are properly configured.
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not self.source_adapter:
            return False, "Source adapter is required"
        if not self.parser:
            return False, "Parser is required"
        if not self.loader:
            return False, "Database loader is required"
        
        # Validate source is accessible
        if not self.source_adapter.validate_source():
            return False, f"Source '{self.source_adapter.get_source_name()}' is not accessible"
        
        return True, None
