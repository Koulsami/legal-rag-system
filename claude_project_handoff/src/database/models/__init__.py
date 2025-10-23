"""
Legal Diagnostic RAG - Database Models Package
"""

from .base import (
    Base,
    DatabaseManager,
    TimestampMixin,
    init_db,
    get_session,
    db_manager
)

from .document import (
    Document,
    DocType,
    Outcome
)

from .interpretation_link import (
    InterpretationLink,
    InterpretationType,
    Authority,
    InterpretationLinkBuilder
)

from .tree_utils import (
    TreeNode,
    TreeTraversal,
    get_complete_provision_for_retrieval,
    visualize_document_tree
)

__version__ = "1.0.0"

__all__ = [
    # Base
    "Base",
    "DatabaseManager",
    "TimestampMixin",
    "init_db",
    "get_session",
    "db_manager",
    
    # Document
    "Document",
    "DocType",
    "Outcome",
    
    # Interpretation Links
    "InterpretationLink",
    "InterpretationType",
    "Authority",
    "InterpretationLinkBuilder",
    
    # Tree Utils
    "TreeNode",
    "TreeTraversal",
    "get_complete_provision_for_retrieval",
    "visualize_document_tree",
]
