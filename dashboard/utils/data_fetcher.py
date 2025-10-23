"""
Data fetcher for dashboard queries.
"""

from datetime import datetime, timedelta
from typing import Dict
import pandas as pd
from sqlalchemy import func, and_
from sqlalchemy.orm import Session

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

from dashboard.models.validation_result_model import ValidationResult


class DashboardDataFetcher:
    """Fetch and aggregate data for dashboard components"""
    
    def __init__(self, db_session: Session):
        self.db = db_session
    
    def get_kpi_metrics(self, days: int = 7) -> Dict:
        """Get key performance indicators"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        total = self.db.query(func.count(ValidationResult.id)).filter(
            ValidationResult.created_at >= cutoff_date
        ).scalar() or 0
        
        pass_count = self.db.query(func.count(ValidationResult.id)).filter(
            and_(ValidationResult.created_at >= cutoff_date, ValidationResult.decision == 'pass')
        ).scalar() or 0
        
        review_count = self.db.query(func.count(ValidationResult.id)).filter(
            and_(ValidationResult.created_at >= cutoff_date, ValidationResult.decision == 'review')
        ).scalar() or 0
        
        reject_count = self.db.query(func.count(ValidationResult.id)).filter(
            and_(ValidationResult.created_at >= cutoff_date, ValidationResult.decision == 'reject')
        ).scalar() or 0
        
        avg_scores = self.db.query(
            func.avg(ValidationResult.synthesis_score).label('synthesis'),
            func.avg(ValidationResult.citation_score).label('citation'),
            func.avg(ValidationResult.hallucination_rate).label('hallucination')
        ).filter(ValidationResult.created_at >= cutoff_date).first()
        
        perf = self.db.query(
            func.avg(ValidationResult.total_time_ms).label('avg_latency')
        ).filter(ValidationResult.created_at >= cutoff_date).first()
        
        pass_rate = (pass_count / total * 100) if total > 0 else 0
        review_rate = (review_count / total * 100) if total > 0 else 0
        reject_rate = (reject_count / total * 100) if total > 0 else 0
        
        return {
            'total_validations': total,
            'pass_count': pass_count,
            'review_count': review_count,
            'reject_count': reject_count,
            'pass_rate': pass_rate,
            'review_rate': review_rate,
            'reject_rate': reject_rate,
            'avg_synthesis_score': avg_scores.synthesis or 0,
            'avg_citation_score': avg_scores.citation or 0,
            'avg_hallucination_rate': avg_scores.hallucination or 0,
            'avg_latency_ms': perf.avg_latency or 0,
            'p95_latency_ms': perf.avg_latency or 0
        }
    
    def get_decision_breakdown(self, days: int = 7) -> pd.DataFrame:
        """Get decision breakdown for pie chart"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        results = self.db.query(
            ValidationResult.decision,
            func.count(ValidationResult.id).label('count')
        ).filter(
            ValidationResult.created_at >= cutoff_date
        ).group_by(ValidationResult.decision).all()
        
        return pd.DataFrame(results, columns=['decision', 'count'])
    
    def get_priority_breakdown(self, days: int = 7) -> pd.DataFrame:
        """Get priority breakdown for review queue"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        results = self.db.query(
            ValidationResult.priority,
            func.count(ValidationResult.id).label('count')
        ).filter(
            and_(ValidationResult.created_at >= cutoff_date, ValidationResult.decision == 'review')
        ).group_by(ValidationResult.priority).all()
        
        # Return simple DataFrame without categorical conversion
        df = pd.DataFrame(results, columns=['priority', 'count'])
        return df
