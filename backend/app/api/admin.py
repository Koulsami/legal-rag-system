"""Admin endpoints"""
from fastapi import APIRouter

router = APIRouter()

@router.get("/stats")
async def get_system_stats():
    """Get system statistics"""
    return {
        "total_users": 0,
        "total_queries": 0,
        "interpretation_links": 0
    }
