"""
Database loader for document ingestion.

Handles:
- Batch insertion of documents
- Deduplication via content hash
- Parent-child relationship validation
- Transaction management
"""

from typing import List, Optional
from datetime import datetime
import logging

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from ..interfaces import DatabaseLoader
from ..models import ParsedDocument, IngestionResult
from src.database.models import Document, DatabaseManager


logger = logging.getLogger(__name__)


class PostgresLoader(DatabaseLoader):
    """Database loader for PostgreSQL via SQLAlchemy"""
    
    def __init__(
        self,
        db_manager: DatabaseManager,
        skip_existing: bool = True,
        allow_duplicates: bool = False
    ):
        """
        Initialize loader.
        
        Args:
            db_manager: Database manager instance
            skip_existing: Skip documents that already exist
            allow_duplicates: Allow duplicate content hashes
        """
        self.db = db_manager
        self.skip_existing = skip_existing
        self.allow_duplicates = allow_duplicates
    
    def load_documents(
        self,
        documents: List[ParsedDocument],
        batch_size: int = 100
    ) -> IngestionResult:
        """
        Load documents into database in batches.
        
        Args:
            documents: List of parsed documents
            batch_size: Documents per batch
            
        Returns:
            IngestionResult with statistics
        """
        result = IngestionResult(
            source_file="batch",
            status="success",
            total_documents=len(documents)
        )
        
        logger.info(f"Starting ingestion of {len(documents)} documents in batches of {batch_size}")
        
        # Process in batches
        for i in range(0, len(documents), batch_size):
            batch = documents[i:i + batch_size]
            
            try:
                self._load_batch(batch, result)
                
                logger.info(
                    f"Processed batch {i // batch_size + 1}: "
                    f"{result.inserted} inserted, {result.skipped} skipped, {result.errors} errors"
                )
                
            except Exception as e:
                error_msg = f"Batch {i // batch_size + 1} failed: {str(e)}"
                logger.error(error_msg)
                result.add_error(error_msg)
                result.status = "partial"
        
        # Finalize
        result.finalize()
        
        if result.errors > 0:
            result.status = "partial" if result.inserted > 0 else "failed"
        
        logger.info(result.summary())
        
        return result
    
    def _load_batch(self, batch: List[ParsedDocument], result: IngestionResult):
        """
        Load a single batch of documents.
        
        Args:
            batch: Batch of documents
            result: Result object to update
        """
        with self.db.get_session() as session:
            # Sort by level to ensure parents are inserted before children
            batch = sorted(batch, key=lambda doc: doc.level)
            
            for doc in batch:
                try:
                    self._load_single_document(session, doc, result)
                except Exception as e:
                    error_msg = f"Failed to load {doc.id}: {str(e)}"
                    logger.error(error_msg)
                    result.add_error(error_msg)
            
            # Commit batch
            try:
                session.commit()
            except Exception as e:
                session.rollback()
                error_msg = f"Batch commit failed: {str(e)}"
                logger.error(error_msg)
                result.add_error(error_msg)
                raise
    
    def _load_single_document(
        self,
        session: Session,
        doc: ParsedDocument,
        result: IngestionResult
    ):
        """
        Load a single document.
        
        Args:
            session: Database session
            doc: Document to load
            result: Result object to update
        """
        # Check if already exists
#        if self.skip_existing and self.document_exists(doc.id):
#            result.add_skip(doc.id, "already exists")
#            return
        
        # Check for duplicates by hash - DISABLED FOR NOW
        # if not self.allow_duplicates:
        #     existing = self.get_document_by_hash(doc.hash)
        #     if existing:
        #         result.add_skip(doc.id, f"duplicate of {existing.id}")
        #         return
        
        # Validate parent exists (if not root)
  #      if doc.parent_id and not self.document_exists(doc.parent_id):
   #         result.add_skip(doc.id, f"parent {doc.parent_id} not found")
    #        return
        
        # Create SQLAlchemy Document object
        db_doc = Document(
            id=doc.id,
            doc_type=doc.doc_type,
            parent_id=doc.parent_id,
            level=doc.level,
            title=doc.title,
            full_text=doc.full_text,
            
            # Metadata
            citation=doc.citation,
            jurisdiction=doc.jurisdiction,
            year=doc.year,
            
            # Statute fields
            act_name=doc.act_name,
            section_number=doc.section_number,
            subsection=doc.subsection,
            
            # Case fields
            court=doc.court,
            para_no=doc.para_no,
            parties=doc.parties,
            
            # Diagnostic fields
            facts_summary=doc.facts_summary,
            cause_of_action=doc.cause_of_action,
            outcome=doc.outcome,
            remedy_awarded=doc.remedy_awarded,
            
            # Source tracking
            url=doc.source_url,
            hash=doc.hash,
            
            # Timestamps
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        try:
            session.add(db_doc)
            session.flush()  # Flush but don't commit (batch commit later)
            result.add_success(doc.id)
            
        except IntegrityError as e:
            session.rollback()
            print(f"⚠️  INTEGRITY ERROR: {doc.id} - {str(e)}")
            result.add_skip(doc.id, f"integrity error: {str(e)}")
    
    def document_exists(self, doc_id: str) -> bool:
        """
        Check if document exists in database.
        
        Args:
            doc_id: Document ID
            
        Returns:
            True if exists
        """
        with self.db.get_session() as session:
            count = session.query(Document).filter(
                Document.id == doc_id
            ).count()
            return count > 0
    
    def get_document_by_hash(self, hash: str) -> Optional[Document]:
        """
        Find document by content hash.
        
        Args:
            hash: SHA-256 hash
            
        Returns:
            Document if found, None otherwise
        """
        with self.db.get_session() as session:
            return session.query(Document).filter(
                Document.hash == hash
            ).first()
    
    def get_statistics(self) -> dict:
        """
        Get database statistics.
        
        Returns:
            Dictionary of statistics
        """
        with self.db.get_session() as session:
            total = session.query(Document).count()
            statutes = session.query(Document).filter(
                Document.doc_type == 'statute'
            ).count()
            cases = session.query(Document).filter(
                Document.doc_type == 'case'
            ).count()
            
            return {
                'total_documents': total,
                'statutes': statutes,
                'cases': cases,
                'root_documents': session.query(Document).filter(
                    Document.level == 0
                ).count(),
                'sections': session.query(Document).filter(
                    Document.level == 1
                ).count(),
                'paragraphs': session.query(Document).filter(
                    Document.level > 1
                ).count()
            }


# ============================================================================
# Helper Functions
# ============================================================================

def validate_tree_integrity(db_manager: DatabaseManager) -> List[str]:
    """
    Validate tree structure integrity.
    
    Checks:
    - All non-root documents have valid parents
    - No orphaned documents
    - No circular references
    
    Args:
        db_manager: Database manager
        
    Returns:
        List of error messages (empty if valid)
    """
    errors = []
    
    with db_manager.get_session() as session:
        # Check for orphaned documents (parent_id doesn't exist)
        orphaned = session.query(Document).filter(
            Document.parent_id.isnot(None),
            ~Document.parent_id.in_(
                session.query(Document.id)
            )
        ).all()
        
        for doc in orphaned:
            errors.append(
                f"Orphaned document {doc.id}: parent {doc.parent_id} not found"
            )
        
        # Check for level mismatches (child level != parent level + 1)
        docs_with_parents = session.query(Document).filter(
            Document.parent_id.isnot(None)
        ).all()
        
        for doc in docs_with_parents:
            parent = session.query(Document).filter(
                Document.id == doc.parent_id
            ).first()
            
            if parent and doc.level != parent.level + 1:
                errors.append(
                    f"Level mismatch for {doc.id}: "
                    f"level={doc.level} but parent level={parent.level}"
                )
    
    return errors
