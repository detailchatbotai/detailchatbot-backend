"""
User management router - placeholder for future implementation.
Will handle user profile operations.
"""

from fastapi import APIRouter

router = APIRouter()

@router.get("/profile")
async def get_user_profile():
    """Placeholder endpoint for user profile"""
    return {"message": "User profile management coming soon"}