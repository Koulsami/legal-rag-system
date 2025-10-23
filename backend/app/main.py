"""
Myk Raws Legal RAG API - Main Application
FastAPI backend for statutory interpretation RAG system
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
import time
import logging
from contextlib import asynccontextmanager

from app.api import auth, chat, user, admin
from app.core.config import settings
from app.core.database import engine, Base
from app.services.retrieval import retrieval_service
from app.services.interpretation_links import interpretation_link_service

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    # Startup
    logger.info("🚀 Starting Myk Raws Legal RAG API...")
    
    # Create database tables
    Base.metadata.create_all(bind=engine)
    logger.info("✅ Database tables created")
    
    # Initialize retrieval service (load FAISS index, embeddings)
    await retrieval_service.initialize()
    logger.info("✅ Retrieval service initialized")
    
    # Load interpretation links
    await interpretation_link_service.initialize()
    logger.info("✅ Interpretation links loaded")
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down Myk Raws API...")
    await retrieval_service.cleanup()


# Create FastAPI application
app = FastAPI(
    title="Myk Raws Legal RAG API",
    version="1.0.0",
    description="AI Legal Assistant for Singapore Statutory Interpretation",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    lifespan=lifespan
)


# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID"]
)


# Compression middleware
app.add_middleware(GZipMiddleware, minimum_size=1000)


# Request ID middleware
@app.middleware("http")
async def add_request_id(request: Request, call_next):
    """Add unique request ID for tracing"""
    import uuid
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Process-Time"] = str(process_time)
    
    logger.info(
        f"Request {request_id}: {request.method} {request.url.path} "
        f"- {response.status_code} - {process_time:.3f}s"
    )
    
    return response


# Error handling
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global error handler"""
    logger.error(f"Unhandled error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": str(exc) if settings.DEBUG else "An error occurred",
            "request_id": getattr(request.state, "request_id", None)
        }
    )


# Include API routers
app.include_router(
    auth.router,
    prefix="/api/auth",
    tags=["Authentication"]
)

app.include_router(
    chat.router,
    prefix="/api/chat",
    tags=["Chat & Query"]
)

app.include_router(
    user.router,
    prefix="/api/user",
    tags=["User Management"]
)

app.include_router(
    admin.router,
    prefix="/api/admin",
    tags=["Admin Operations"]
)


# Health check endpoints
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Myk Raws Legal RAG API",
        "version": "1.0.0",
        "status": "operational",
        "docs": "/api/docs"
    }


@app.get("/health")
async def health_check():
    """Health check for monitoring"""
    return {
        "status": "healthy",
        "database": "connected",
        "retrieval_service": retrieval_service.is_ready(),
        "interpretation_links": interpretation_link_service.is_ready()
    }


@app.get("/api/status")
async def status():
    """Detailed status information"""
    return {
        "api_version": "1.0.0",
        "environment": settings.ENVIRONMENT,
        "features": {
            "retrieval": retrieval_service.is_ready(),
            "interpretation_links": interpretation_link_service.is_ready(),
            "hybrid_search": True,
            "lepard_classification": True
        },
        "metrics": {
            "interpretation_links_count": interpretation_link_service.get_link_count(),
            "indexed_documents": retrieval_service.get_document_count()
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        workers=1 if settings.DEBUG else 4,
        log_level="info"
    )
