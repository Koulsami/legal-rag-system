"""
Database model for storing validation results.
Part of Week 5 Day 5: Dashboard & Reporting
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import Column, Integer, String, Float, Text, DateTime, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session

Base = declarative_base()


class ValidationResult(Base):
    """Store validation results for dashboard and analytics"""
    
    __tablename__ = 'validation_results'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    query = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    correlation_id = Column(String(100), index=True)
    decision = Column(String(20), nullable=False, index=True)
    priority = Column(String(20), index=True)
    synthesis_score = Column(Float)
    citation_score = Column(Float)
    hallucination_rate = Column(Float)
    total_time_ms = Column(Float)
    synthesis_time_ms = Column(Float)
    citation_time_ms = Column(Float)
    hallucination_time_ms = Column(Float)
    total_citations = Column(Integer, default=0)
    verified_citations = Column(Integer, default=0)
    interpretation_citations = Column(Integer, default=0)
    validation_details = Column(JSON)
    review_status = Column(String(20), default='pending')
    reviewer_id = Column(String(100))
    reviewer_feedback = Column(Text)
    reviewed_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<ValidationResult(id={self.id}, decision={self.decision})>"
    
    def to_dict(self):
        return {
            'id': self.id,
            'query': self.query,
            'decision': self.decision,
            'priority': self.priority,
            'scores': {
                'synthesis': self.synthesis_score,
                'citation': self.citation_score,
                'hallucination_rate': self.hallucination_rate
            }
        }
