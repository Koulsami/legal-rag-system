"""
FastAPI Main Application
Complete implementation with validation endpoints
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from api.utils.database import get_db, verify_db_connection, get_db_info
from api.endpoints import validate
from validation.logging_config import get_logger

logger = get_logger(__name__)

# ============================================================================
# Lifespan Context Manager
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events"""
    # Startup
    logger.info("Starting Legal RAG Validation API")
    try:
        verify_db_connection()
        logger.info("Database connection verified")
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Legal RAG Validation API")

# ============================================================================
# FastAPI App
# ============================================================================

app = FastAPI(
    title="Legal RAG Validation API",
    description="API for validating legal RAG system answers",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan
)

# ============================================================================
# CORS Middleware
# ============================================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# Health Check
# ============================================================================

@app.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """
    Health check endpoint
    
    Returns:
        dict: System health status
    """
    try:
        # Verify database connection
        db.execute("SELECT 1")
        db_status = "healthy"
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        db_status = "unhealthy"
    
    return {
        "status": "healthy" if db_status == "healthy" else "degraded",
        "database": db_status,
        "version": "1.0.0"
    }


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Legal RAG Validation API",
        "version": "1.0.0",
        "docs": "/api/docs"
    }


@app.get("/api/info")
async def api_info():
    """
    Get API information
    
    Returns:
        dict: API and database info
    """
    try:
        db_info = get_db_info()
    except Exception as e:
        logger.error(f"Failed to get DB info: {e}")
        db_info = {"error": str(e)}
    
    return {
        "api_version": "1.0.0",
        "database": db_info,
        "endpoints": [
            "/health",
            "/api/info",
            "/api/v1/validate",
            "/api/v1/validate/batch"
        ]
    }


# ============================================================================
# Include Routers
# ============================================================================

# Validation endpoints
app.include_router(
    validate.router,
    prefix="/api/v1",
    tags=["validation"]
)

# ============================================================================
# Startup/Shutdown Events
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Startup event handler"""
    logger.info("Starting Legal RAG Validation API")
    
    try:
        verify_db_connection()
        logger.info("Database connection verified")
    except Exception as e:
        logger.error(f"Database connection failed: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown event handler"""
    logger.info("Shutting down Legal RAG Validation API")


# ============================================================================
# Exception Handlers
# ============================================================================

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    logger.error(
        f"Unhandled exception: {exc}",
        exc_info=True
    )
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
