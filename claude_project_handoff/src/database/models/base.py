"""
Database configuration and base models for Legal Diagnostic RAG.
"""

from typing import Any, Dict, Optional
from datetime import datetime
from contextlib import contextmanager

from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker, declared_attr
from sqlalchemy import Column, DateTime
import logging

logger = logging.getLogger(__name__)

NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}

metadata = MetaData(naming_convention=NAMING_CONVENTION)

class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""
    metadata = metadata
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model instance to dictionary."""
        return {
            column.name: getattr(self, column.name)
            for column in self.__table__.columns
        }
    
    def __repr__(self) -> str:
        """String representation of model instance."""
        attrs = ', '.join(
            f"{key}={getattr(self, key)!r}"
            for key in list(self.__table__.columns.keys())[:3]
        )
        return f"{self.__class__.__name__}({attrs})"

class TimestampMixin:
    """Mixin for created_at and updated_at timestamps."""
    
    @declared_attr
    def created_at(cls):
        """Timestamp when record was created."""
        return Column(DateTime, nullable=False, default=datetime.utcnow)
    
    @declared_attr
    def updated_at(cls):
        """Timestamp when record was last updated."""
        return Column(
            DateTime,
            nullable=False,
            default=datetime.utcnow,
            onupdate=datetime.utcnow
        )

class DatabaseManager:
    """Manages database connections and sessions."""
    
    def __init__(self, database_url: str, echo: bool = False, pool_size: int = 5, max_overflow: int = 10):
        """Initialize database manager."""
        self.database_url = database_url
        
        self.engine = create_engine(
            database_url,
            echo=echo,
            pool_size=pool_size,
            max_overflow=max_overflow,
            pool_pre_ping=True,
        )
        
        self.SessionLocal = sessionmaker(
            bind=self.engine,
            autocommit=False,
            autoflush=False,
            expire_on_commit=False
        )
        
        self._setup_extensions()
        logger.info(f"Database manager initialized")
    
    def _setup_extensions(self) -> None:
        """Enable required PostgreSQL extensions."""
        from sqlalchemy import text
        with self.engine.connect() as conn:
            try:
                conn.execute(text("CREATE EXTENSION IF NOT EXISTS pg_trgm"))
                conn.execute(text('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"'))
                conn.commit()
                logger.info("PostgreSQL extensions enabled")
            except Exception as e:
                logger.warning(f"Could not enable extensions: {e}")

            
    def create_all(self) -> None:
        """Create all tables in the database."""
        Base.metadata.create_all(self.engine)
        logger.info("Database tables created")
    
    def drop_all(self) -> None:
        """Drop all tables. USE WITH CAUTION!"""
        Base.metadata.drop_all(self.engine)
        logger.warning("All database tables dropped")
    
    @contextmanager
    def get_session(self):
        """Context manager for database sessions."""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Session error: {e}")
            raise
        finally:
            session.close()

db_manager: Optional[DatabaseManager] = None

def init_db(database_url: str, **kwargs) -> DatabaseManager:
    """Initialize global database manager."""
    global db_manager
    db_manager = DatabaseManager(database_url, **kwargs)
    return db_manager

def get_session() -> Session:
    """Get a database session from global manager."""
    if db_manager is None:
        raise RuntimeError("Database manager not initialized. Call init_db() first.")
    return db_manager.SessionLocal()
