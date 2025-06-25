from app.services.auth_service import AuthService, AuthServiceException
from app.models.user import User
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any
from fastapi import HTTPException
import logging
from sqlalchemy.exc import IntegrityError

class UserService:
    logger = logging.getLogger(__name__)

    @staticmethod
    async def create_local_user(
        db: AsyncSession,
        *,
        email: str,
        shop_name: str,
        plan: str,
        is_subscribed: bool,
        supabase_user_id: str
    ) -> User | None:
        """
        Create a user in the local users table after successful Supabase Auth signup.
        Returns the user if successful, or None if a unique constraint is violated.
        """
        UserService.logger.info(f"[DB] Start create_local_user for email: {email}, shop: {shop_name}")
        new_user = User(
            email=email,
            hashed_password="supabase_managed",
            shop_name=shop_name,
            plan=plan,
            is_subscribed=is_subscribed,
            is_active=True,
            supabase_user_id=supabase_user_id
        )
        db.add(new_user)
        try:
            await db.commit()
            await db.refresh(new_user)
            UserService.logger.info(f"[DB] Successfully inserted user: {email}")
            return new_user
        except IntegrityError as e:
            await db.rollback()
            UserService.logger.warning(f"[DB] IntegrityError (likely duplicate) for {email}: {e}")
            return None
        except Exception as e:
            await db.rollback()
            UserService.logger.error(f"[DB] Insert failed for {email}: {e}")
            raise

    @staticmethod
    async def signup_user(
        db: AsyncSession,
        *,
        user_create: Any,
        auth_service: AuthService
    ) -> dict:
        """
        Orchestrates user signup: registers with Supabase Auth, then creates a local user.
        Handles duplicate and unexpected errors with clear logging and HTTP responses.
        """
        UserService.logger.info(f"[Signup] Start signup_user for email: {user_create.email}")
        try:
            # Register with Supabase Auth
            result = await auth_service.register_user(
                email=user_create.email,
                password=user_create.password,
                full_name=user_create.shop_name
            )
            supabase_user_id = result.get("id")
            if not supabase_user_id:
                UserService.logger.error(f"[Signup] Supabase user ID not returned for email: {user_create.email}")
                raise HTTPException(status_code=500, detail="Supabase user ID not returned.")
            # Insert into local users table
            local_user = await UserService.create_local_user(
                db,
                email=user_create.email,
                shop_name=user_create.shop_name,
                plan=user_create.plan,
                is_subscribed=user_create.is_subscribed,
                supabase_user_id=supabase_user_id
            )
            if not local_user:
                UserService.logger.warning(f"[Signup] Local DB insert failed (duplicate or constraint) for email: {user_create.email}")
                raise HTTPException(status_code=400, detail="User already exists in local DB or DB error.")
            UserService.logger.info(f"[Signup] Signup complete for email: {user_create.email}")
            return {"message": "User registered successfully", "data": result}
        except AuthServiceException as exc:
            UserService.logger.error(f"[Signup] Supabase AuthServiceException for {user_create.email}: {exc}")
            raise HTTPException(status_code=400, detail=str(exc))
        except Exception as exc:
            UserService.logger.error(f"[Signup] Unexpected error for {user_create.email}: {exc}")
            raise HTTPException(status_code=500, detail="Internal server error")

    @staticmethod
    async def login_user(
        *,
        user_login: Any,
        auth_service: AuthService
    ) -> dict:
        """
        Authenticates a user using Supabase Auth and returns tokens.
        Handles known and unexpected errors with clear logging.
        """
        try:
            result = await auth_service.login_user(
                email=user_login.email,
                password=user_login.password
            )
            return {"message": "Login successful", "data": result}
        except AuthServiceException as exc:
            UserService.logger.error(f"[Login] Supabase AuthServiceException for {user_login.email}: {exc}")
            raise HTTPException(status_code=400, detail=str(exc))
        except Exception as exc:
            UserService.logger.error(f"[Login] Unexpected error for {user_login.email}: {exc}")
            raise HTTPException(status_code=500, detail="Internal server error")
