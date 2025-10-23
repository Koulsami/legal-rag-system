# src/database/connection.py
"""
Database connection management for legal RAG system.
Compatible with SQLAlchemy 2.0+
"""

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator
import os

# Database configuration
DATABASE_URL = os.getenv(
    'DATABASE_URL',
    'postgresql://legal_rag:legal_rag_2025@localhost:5432/legal_rag_dev'
)

# Create engine
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    echo=False
)

# Session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

def get_session() -> Session:
    """Get a database session."""
    return SessionLocal()

def get_db() -> Generator[Session, None, None]:
    """Dependency for FastAPI - yields database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Initialize database - create all tables."""
    from src.database.models.base import Base
    Base.metadata.create_all(bind=engine)
    print("✅ Database initialized successfully")

def drop_all():
    """WARNING: Drops all tables."""
    from src.database.models.base import Base
    Base.metadata.drop_all(bind=engine)
    print("⚠️  All tables dropped")

def test_connection() -> bool:
    """Test database connection."""
    try:
        db = get_session()
        # FIX: Use text() wrapper for SQLAlchemy 2.0
        db.execute(text("SELECT 1"))
        db.close()
        print("✅ Database connection successful")
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

if __name__ == "__main__":
    test_connection()
