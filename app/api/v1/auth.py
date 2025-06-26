from fastapi import APIRouter, HTTPException, status, Depends, Request, Response
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.user import UserCreate, UserLogin
from app.services.auth_service import AuthService, AuthServiceException
from app.services.user_service import UserService
from app.core.database import get_db
from app.models.user import User
from typing import Any
import logging

router = APIRouter(prefix="/auth", tags=["auth"])

auth_service = AuthService()
logger = logging.getLogger(__name__)

@router.post("/signup", status_code=status.HTTP_201_CREATED)
async def signup(user: UserCreate, db: AsyncSession = Depends(get_db)) -> Any:
    """
    Register a new user using Supabase Auth and sync with local users table.
    Delegates all business logic to the UserService for best practice separation of concerns.
    """
    logger.info(f"Signup attempt for email: {user.email}")
    result = await UserService.signup_user(db, user_create=user, auth_service=auth_service)
    logger.info(f"Signup successful for email: {user.email}")
    return result

@router.post("/login", status_code=status.HTTP_200_OK)
async def login(user: UserLogin) -> Any:
    """
    Authenticate a user using Supabase Auth and return access tokens.
    Delegates all business logic to the UserService for best practice separation of concerns.
    """
    logger.info(f"Login attempt for email: {user.email}")
    result = await UserService.login_user(user_login=user, auth_service=auth_service)
    logger.info(f"Login successful for email: {user.email}")
    return result

@router.delete("/me", status_code=204)
async def delete_account(
    db: AsyncSession = Depends(get_db),
    supabase_user_id: str = Depends(AuthService.get_current_user_supabase_id)
):
    """
    Delete the authenticated user's account from Supabase Auth and the local DB.
    """
    await UserService.delete_account(db, supabase_user_id, auth_service)
    return Response(status_code=204)
