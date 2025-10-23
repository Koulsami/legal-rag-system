"""
API Authentication
Implements API key-based auth as per Patent Claim 17
"""
from fastapi import Security, HTTPException, status
from fastapi.security import APIKeyHeader
from typing import Optional
import os
from datetime import datetime

API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

# In production, use environment variables or secret manager
VALID_API_KEYS = {
    "dev_key_12345": {
        "type": "development",
        "rate_limit": 1000,  # requests per hour
        "created": "2025-01-01"
    },
    "prod_key_67890": {
        "type": "production",
        "rate_limit": 10000,
        "created": "2025-01-01"
    }
}

# Load from environment if available
ENV_API_KEY = os.getenv("API_KEY")
if ENV_API_KEY:
    VALID_API_KEYS[ENV_API_KEY] = {
        "type": "environment",
        "rate_limit": 10000,
        "created": datetime.now().isoformat()
    }


async def verify_api_key(api_key: Optional[str] = Security(api_key_header)) -> dict:
    """
    Verify API key and return key metadata
    
    Args:
        api_key: API key from header
        
    Returns:
        dict: API key metadata
        
    Raises:
        HTTPException: If key is missing or invalid
    """
    if api_key is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API key. Include 'X-API-Key' header.",
            headers={"WWW-Authenticate": "ApiKey"}
        )
    
    if api_key not in VALID_API_KEYS:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "ApiKey"}
        )
    
    return VALID_API_KEYS[api_key]


def get_api_key_type(api_key_metadata: dict) -> str:
    """Extract API key type from metadata"""
    return api_key_metadata.get("type", "unknown")


def get_rate_limit(api_key_metadata: dict) -> int:
    """Extract rate limit from API key metadata"""
    return api_key_metadata.get("rate_limit", 100)
