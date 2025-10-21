"""User management endpoints"""
from fastapi import APIRouter, Depends
from app.core.dependencies import get_current_user
from app.database.models import User

router = APIRouter()

@router.get("/me")
async def get_current_user_profile(current_user: User = Depends(get_current_user)):
    """Get current user profile"""
    return {
        "id": current_user.id,
        "email": current_user.email,
        "name": current_user.name,
        "is_active": current_user.is_active
    }
