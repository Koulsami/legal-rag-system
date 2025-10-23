"""
Database utilities for FastAPI
Provides session management and dependency injection
"""
from typing import Generator
from sqlalchemy.orm import Session
from sqlalchemy import text

from src.database.connection import get_session
from validation.logging_config import get_logger

logger = get_logger(__name__)


def get_db() -> Generator[Session, None, None]:
    """
    Dependency injection for database sessions
    
    Yields:
        Session: SQLAlchemy session
        
    Usage:
        @app.get("/items")
        def get_items(db: Session = Depends(get_db)):
            return db.query(Item).all()
    """
    db = get_session()
    try:
        yield db
    finally:
        db.close()


def verify_db_connection() -> bool:
    """
    Verify database connection is working
    
    Returns:
        bool: True if connection successful
        
    Raises:
        Exception: If connection fails
    """
    try:
        db = get_session()
        # Use text() for SQLAlchemy 2.0 compatibility
        db.execute(text("SELECT 1"))
        db.close()
        logger.info("Database connection verified")
        return True
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        raise


def get_db_info() -> dict:
    """
    Get database connection information
    
    Returns:
        dict: Database metadata
    """
    try:
        db = get_session()
        engine = db.bind
        
        info = {
            "driver": str(engine.driver),
            "database": engine.url.database,
            "host": engine.url.host,
            "port": engine.url.port,
        }
        
        # Try to get pool info (may not be available)
        try:
            info["pool_size"] = engine.pool.size()
            info["pool_overflow"] = engine.pool.overflow()
        except:
            pass
        
        db.close()
        return info
    except Exception as e:
        logger.error(f"Failed to get DB info: {e}")
        return {"error": str(e)}
