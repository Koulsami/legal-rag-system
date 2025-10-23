"""
Tree traversal utilities for hierarchical document structure.
"""

from typing import List, Optional, Dict, Any
from dataclasses import dataclass

from sqlalchemy import text
from sqlalchemy.orm import Session

# Import will be available after all models are created
# Using string reference to avoid circular imports
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .document import Document


@dataclass
class TreeNode:
    """Represents a node in the document tree."""
    document: "Document"
    parent: Optional["TreeNode"] = None
    children: List["TreeNode"] = None
    level: int = 0
    
    def __post_init__(self):
        if self.children is None:
            self.children = []
    
    def add_child(self, child: "TreeNode") -> None:
        """Add a child node."""
        child.parent = self
        self.children.append(child)
    
    def is_root(self) -> bool:
        """Check if this is a root node."""
        return self.parent is None
    
    def is_leaf(self) -> bool:
        """Check if this is a leaf node."""
        return len(self.children) == 0
    
    def get_path(self) -> List["TreeNode"]:
        """Get path from root to this node."""
        path = []
        current = self
        while current:
            path.insert(0, current)
            current = current.parent
        return path
    
    def get_depth(self) -> int:
        """Get depth of this node."""
        depth = 0
        current = self.parent
        while current:
            depth += 1
            current = current.parent
        return depth


class TreeTraversal:
    """Utilities for traversing document tree structures."""
    
    def __init__(self, session: Session):
        """Initialize tree traversal utilities."""
        self.session = session
    
    def get_parent(self, doc_id: str) -> Optional["Document"]:
        """Get parent document using SQL function."""
        # Import here to avoid circular import
        from .document import Document
        
        result = self.session.execute(
            text("SELECT * FROM get_parent(:doc_id)"),
            {"doc_id": doc_id}
        ).first()
        
        if not result:
            return None
        
        return self.session.query(Document).filter_by(id=result.id).first()
    
    def get_siblings(self, doc_id: str) -> List["Document"]:
        """Get sibling documents using SQL function."""
        from .document import Document
        
        result = self.session.execute(
            text("SELECT * FROM get_siblings(:doc_id)"),
            {"doc_id": doc_id}
        ).all()
        
        if not result:
            return []
        
        sibling_ids = [row.id for row in result]
        return self.session.query(Document).filter(
            Document.id.in_(sibling_ids)
        ).all()
    
    def get_children(self, doc_id: str) -> List["Document"]:
        """Get child documents using SQL function."""
        from .document import Document
        
        result = self.session.execute(
            text("SELECT * FROM get_children(:doc_id)"),
            {"doc_id": doc_id}
        ).all()
        
        if not result:
            return []
        
        child_ids = [row.id for row in result]
        return self.session.query(Document).filter(
            Document.id.in_(child_ids)
        ).order_by(Document.id).all()
    
    def build_complete_provision(self, doc_id: str) -> str:
        """Build complete provision text using SQL function."""
        result = self.session.execute(
            text("SELECT build_complete_provision(:doc_id) as text"),
            {"doc_id": doc_id}
        ).scalar()
        
        return result or ""
    
    def get_root(self, doc_id: str) -> Optional["Document"]:
        """Get root document by traversing up the tree."""
        from .document import Document
        
        doc = self.session.query(Document).filter_by(id=doc_id).first()
        if not doc:
            return None
        
        while doc.parent_id:
            doc = self.session.query(Document).filter_by(id=doc.parent_id).first()
            if not doc:
                break
        
        return doc
    
    def get_ancestors(self, doc_id: str) -> List["Document"]:
        """Get all ancestor documents from immediate parent to root."""
        from .document import Document
        
        ancestors = []
        doc = self.session.query(Document).filter_by(id=doc_id).first()
        
        if not doc:
            return []
        
        while doc.parent_id:
            parent = self.session.query(Document).filter_by(id=doc.parent_id).first()
            if parent:
                ancestors.append(parent)
                doc = parent
            else:
                break
        
        return ancestors
    
    def get_descendants(self, doc_id: str, max_depth: Optional[int] = None) -> List["Document"]:
        """Get all descendant documents."""
        from .document import Document
        
        doc = self.session.query(Document).filter_by(id=doc_id).first()
        if not doc:
            return []
        
        descendants = []
        
        def _traverse(current: "Document", depth: int = 0):
            if max_depth is not None and depth >= max_depth:
                return
            
            children = self.get_children(current.id)
            for child in children:
                descendants.append(child)
                _traverse(child, depth + 1)
        
        _traverse(doc)
        return descendants
    
    def build_tree(self, root_id: str) -> Optional[TreeNode]:
        """Build complete tree structure starting from root."""
        from .document import Document
        
        root_doc = self.session.query(Document).filter_by(id=root_id).first()
        if not root_doc:
            return None
        
        root_node = TreeNode(document=root_doc, level=0)
        
        def _build_subtree(node: TreeNode):
            children = self.get_children(node.document.id)
            for child_doc in children:
                child_node = TreeNode(document=child_doc, level=node.level + 1)
                node.add_child(child_node)
                _build_subtree(child_node)
        
        _build_subtree(root_node)
        return root_node
    
    def enrich_with_context(self, doc_id: str, include_parent: bool = True,
                          include_siblings: bool = True,
                          include_children: bool = True) -> Dict[str, Any]:
        """Enrich a document with hierarchical context."""
        from .document import Document
        
        doc = self.session.query(Document).filter_by(id=doc_id).first()
        if not doc:
            return {}
        
        result = {
            'document': doc,
            'parent': None,
            'siblings': [],
            'children': [],
            'complete_provision': '',
            'breadcrumb': []
        }
        
        if include_parent and doc.parent_id:
            result['parent'] = self.get_parent(doc_id)
        
        if include_siblings:
            result['siblings'] = self.get_siblings(doc_id)
        
        if include_children:
            result['children'] = self.get_children(doc_id)
        
        if doc.is_statute:
            result['complete_provision'] = self.build_complete_provision(doc_id)
        
        ancestors = self.get_ancestors(doc_id)
        ancestors.reverse()
        result['breadcrumb'] = [
            a.title or a.section_title or a.id for a in ancestors
        ] + [doc.title or doc.section_title or doc.id]
        
        return result
    
    def visualize_tree(self, root_id: str, max_depth: Optional[int] = None,
                      show_ids: bool = False) -> str:
        """Create ASCII tree visualization."""
        tree = self.build_tree(root_id)
        if not tree:
            return "Document not found"
        
        lines = []
        
        def _visualize_node(node: TreeNode, prefix: str = "", is_last: bool = True):
            if max_depth is not None and node.level > max_depth:
                return
            
            doc = node.document
            label = doc.title or doc.section_title or doc.section_number or doc.id
            if show_ids:
                label = f"{label} ({doc.id})"
            
            connector = "└── " if is_last else "├── "
            if node.level == 0:
                lines.append(label)
            else:
                lines.append(f"{prefix}{connector}{label}")
            
            if node.children:
                new_prefix = prefix + ("    " if is_last else "│   ")
                for i, child in enumerate(node.children):
                    is_last_child = (i == len(node.children) - 1)
                    _visualize_node(child, new_prefix, is_last_child)
        
        _visualize_node(tree)
        return "\n".join(lines)
    
    def bfs_traversal(self, root_id: str) -> List["Document"]:
        """Breadth-first traversal of tree."""
        from .document import Document
        
        root = self.session.query(Document).filter_by(id=root_id).first()
        if not root:
            return []
        
        result = []
        queue = [root]
        
        while queue:
            doc = queue.pop(0)
            result.append(doc)
            
            children = self.get_children(doc.id)
            queue.extend(children)
        
        return result
    
    def dfs_traversal(self, root_id: str) -> List["Document"]:
        """Depth-first traversal of tree."""
        from .document import Document
        
        root = self.session.query(Document).filter_by(id=root_id).first()
        if not root:
            return []
        
        result = []
        
        def _dfs(doc: "Document"):
            result.append(doc)
            children = self.get_children(doc.id)
            for child in children:
                _dfs(child)
        
        _dfs(root)
        return result
    
    def get_all_roots(self) -> List["Document"]:
        """Get all root documents (no parent)."""
        from .document import Document
        
        return self.session.query(Document).filter(
            Document.parent_id.is_(None)
        ).all()
    
    def get_all_leaves(self) -> List["Document"]:
        """Get all leaf documents (no children)."""
        from .document import Document
        
        subquery = self.session.query(Document.parent_id).distinct()
        return self.session.query(Document).filter(
            ~Document.id.in_(subquery)
        ).all()
    
    def validate_tree(self, root_id: str) -> List[str]:
        """Validate tree structure and report issues."""
        from .document import Document
        
        errors = []
        
        root = self.session.query(Document).filter_by(id=root_id).first()
        if not root:
            errors.append(f"Root document '{root_id}' not found")
            return errors
        
        if root.parent_id:
            errors.append(f"Root document '{root_id}' has parent '{root.parent_id}'")
        
        visited = set()
        
        def _validate(doc: "Document", expected_level: int):
            if doc.id in visited:
                errors.append(f"Cycle detected at document '{doc.id}'")
                return
            visited.add(doc.id)
            
            if doc.level != expected_level:
                errors.append(
                    f"Document '{doc.id}' has level {doc.level}, "
                    f"expected {expected_level}"
                )
            
            children = self.get_children(doc.id)
            for child in children:
                if child.parent_id != doc.id:
                    errors.append(
                        f"Child '{child.id}' has parent_id '{child.parent_id}', "
                        f"expected '{doc.id}'"
                    )
                
                _validate(child, expected_level + 1)
        
        _validate(root, 0)
        
        return errors


def get_complete_provision_for_retrieval(session: Session, doc_id: str) -> Dict[str, Any]:
    """Get complete provision with all context for retrieval results."""
    traversal = TreeTraversal(session)
    context = traversal.enrich_with_context(doc_id)
    
    # Rename for clarity
    context['complete_text'] = context.pop('complete_provision', '')
    
    return context


def visualize_document_tree(session: Session, root_id: str,
                           max_depth: Optional[int] = None) -> str:
    """Visualize document tree structure."""
    traversal = TreeTraversal(session)
    return traversal.visualize_tree(root_id, max_depth)
