"""
Review workflow actions for dashboard.
Week 5 Day 5 Part 2: Review Queue
"""

from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

from dashboard.models.validation_result_model import ValidationResult


class ReviewActions:
    """Handle review workflow actions"""
    
    def __init__(self, db_session: Session):
        self.db = db_session
    
    def approve_answer(
        self,
        validation_id: int,
        reviewer_id: str,
        feedback: Optional[str] = None
    ) -> bool:
        """
        Approve a validation result.
        
        Args:
            validation_id: ID of validation result
            reviewer_id: ID/name of reviewer
            feedback: Optional feedback comments
            
        Returns:
            True if successful, False otherwise
        """
        try:
            result = self.db.query(ValidationResult).filter(
                ValidationResult.id == validation_id
            ).first()
            
            if not result:
                return False
            
            result.review_status = 'approved'
            result.reviewer_id = reviewer_id
            result.reviewer_feedback = feedback
            result.reviewed_at = datetime.utcnow()
            
            self.db.commit()
            return True
            
        except Exception as e:
            self.db.rollback()
            print(f"Error approving answer: {e}")
            return False
    
    def reject_answer(
        self,
        validation_id: int,
        reviewer_id: str,
        feedback: str
    ) -> bool:
        """
        Reject a validation result.
        
        Args:
            validation_id: ID of validation result
            reviewer_id: ID/name of reviewer
            feedback: Required rejection reason
            
        Returns:
            True if successful, False otherwise
        """
        try:
            result = self.db.query(ValidationResult).filter(
                ValidationResult.id == validation_id
            ).first()
            
            if not result:
                return False
            
            result.review_status = 'rejected'
            result.reviewer_id = reviewer_id
            result.reviewer_feedback = feedback
            result.reviewed_at = datetime.utcnow()
            
            self.db.commit()
            return True
            
        except Exception as e:
            self.db.rollback()
            print(f"Error rejecting answer: {e}")
            return False
    
    def request_revision(
        self,
        validation_id: int,
        reviewer_id: str,
        feedback: str
    ) -> bool:
        """
        Request revision for a validation result.
        
        Args:
            validation_id: ID of validation result
            reviewer_id: ID/name of reviewer
            feedback: Required revision notes
            
        Returns:
            True if successful, False otherwise
        """
        try:
            result = self.db.query(ValidationResult).filter(
                ValidationResult.id == validation_id
            ).first()
            
            if not result:
                return False
            
            result.review_status = 'revision_requested'
            result.reviewer_id = reviewer_id
            result.reviewer_feedback = feedback
            result.reviewed_at = datetime.utcnow()
            
            self.db.commit()
            return True
            
        except Exception as e:
            self.db.rollback()
            print(f"Error requesting revision: {e}")
            return False
    
    def get_review_stats(self, reviewer_id: Optional[str] = None) -> dict:
        """
        Get review statistics.
        
        Args:
            reviewer_id: Optional filter by reviewer
            
        Returns:
            Dictionary with review statistics
        """
        from sqlalchemy import func
        
        query = self.db.query(
            ValidationResult.review_status,
            func.count(ValidationResult.id).label('count')
        ).filter(
            ValidationResult.decision == 'review'
        )
        
        if reviewer_id:
            query = query.filter(ValidationResult.reviewer_id == reviewer_id)
        
        results = query.group_by(ValidationResult.review_status).all()
        
        stats = {status: count for status, count in results}
        
        return {
            'pending': stats.get('pending', 0),
            'approved': stats.get('approved', 0),
            'rejected': stats.get('rejected', 0),
            'revision_requested': stats.get('revision_requested', 0),
            'total': sum(stats.values())
        }
