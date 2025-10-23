"""Adapter to use existing database models with extraction pipeline"""
from src.database.models.interpretation_link import (
    InterpretationType,
    Authority,
)

# Re-export for extraction pipeline
__all__ = ['InterpretationType', 'Authority']
