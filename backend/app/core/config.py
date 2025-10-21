"""
Configuration settings for Myk Raws Legal RAG API
Environment variables and application settings
"""
from pydantic_settings import BaseSettings
from typing import List, Optional
import os
from pathlib import Path


class Settings(BaseSettings):
    """Application settings from environment variables"""
    
    # Application
    APP_NAME: str = "Myk Raws Legal RAG"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = "production"
    DEBUG: bool = False
    
    # API
    API_V1_PREFIX: str = "/api"
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7
    
    # Database
    DATABASE_URL: str = "postgresql://user:password@localhost:5432/mykraws_legal"
    
    # CORS - Handle both string and list formats
    CORS_ORIGINS: str | List[str] = "http://localhost:3000"
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Convert CORS_ORIGINS to list if it's a string"""
        if isinstance(self.CORS_ORIGINS, str):
            return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]
        return self.CORS_ORIGINS
    
    # OpenAI
    OPENAI_API_KEY: str
    OPENAI_MODEL: str = "gpt-4-turbo-preview"
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-large"
    OPENAI_MAX_TOKENS: int = 3000
    OPENAI_TEMPERATURE: float = 0.1
    
    # Retrieval Settings
    RETRIEVAL_TOP_K: int = 10
    RETRIEVAL_HYBRID_ALPHA: float = 0.5
    RETRIEVAL_MAX_INTERPRETIVE_CASES: int = 3
    RETRIEVAL_SYNTHETIC_BOOST: float = 0.7
    
    # Interpretation Links
    INTERPRETATION_BOOST_BINDING: float = 3.0
    INTERPRETATION_BOOST_PERSUASIVE: float = 2.0
    INTERPRETATION_BOOST_OBITER: float = 1.5
    INTERPRETATION_BOOST_DISSENT: float = 1.2
    
    # FAISS Index
    FAISS_INDEX_PATH: str = "./data/faiss/legal_paragraphs.index"
    FAISS_MAPPING_PATH: str = "./data/faiss/doc_id_mapping.json"
    
    # Data paths
    DATA_DIR: Path = Path("./data")
    STATUTES_PATH: Path = DATA_DIR / "statutes"
    CASES_PATH: Path = DATA_DIR / "cases"
    INTERPRETATION_LINKS_PATH: Path = DATA_DIR / "interpretation_links.json"
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"
    
    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_REQUESTS_PER_MINUTE: int = 20
    RATE_LIMIT_REQUESTS_PER_HOUR: int = 100
    
    # Quality Thresholds
    MIN_SYNTHESIS_QUALITY_SCORE: float = 0.8
    MAX_HALLUCINATION_RATE: float = 0.05
    MIN_CITATION_PRECISION: float = 0.95
    
    # Features
    ENABLE_LEPARD_CLASSIFICATION: bool = True
    ENABLE_INTERPRETATION_LINKS: bool = True
    ENABLE_HYBRID_RETRIEVAL: bool = True
    ENABLE_QUERY_REWRITING: bool = True
    
    # Monitoring
    SENTRY_DSN: Optional[str] = None
    ENABLE_METRICS: bool = True
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Create settings instance
settings = Settings()


# Validation
def validate_settings():
    """Validate critical settings"""
    errors = []
    
    if not settings.SECRET_KEY or len(settings.SECRET_KEY) < 32:
        errors.append("SECRET_KEY must be at least 32 characters")
    
    if not settings.OPENAI_API_KEY or settings.OPENAI_API_KEY == "sk-YOUR-KEY-HERE":
        errors.append("OPENAI_API_KEY is required and must be set to a valid key")
    
    if errors:
        raise ValueError(f"Configuration errors: {', '.join(errors)}")


# Only validate if not in test mode
if os.getenv("TESTING") != "true":
    try:
        validate_settings()
    except ValueError as e:
        print(f"⚠️  Configuration Warning: {e}")
        print("⚠️  Some features may not work until configuration is fixed")
