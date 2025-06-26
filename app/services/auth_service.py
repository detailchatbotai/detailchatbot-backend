import httpx
import logging
from typing import Any, Dict, Optional
from fastapi import HTTPException, Request
from jose import jwt, JWTError
from app.core.config import settings

class AuthServiceException(Exception):
    """Custom exception for AuthService errors."""
    pass

class AuthService:
    """
    Service for handling authentication with Supabase.
    """
    def __init__(self):
        self.supabase_url = settings.SUPABASE_URL
        self.supabase_key = settings.SUPABASE_KEY

    async def register_user(self, email: str, password: str, full_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Register a new user with Supabase Auth.
        """
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.supabase_url}/auth/v1/signup",
                    headers={
                        "apikey": self.supabase_key,
                        "Content-Type": "application/json"
                    },
                    json={
                        "email": email,
                        "password": password,
                        "data": {"full_name": full_name}
                    }
                )
                response.raise_for_status()
                resp_json = response.json()
                logging.getLogger(__name__).info(f"Supabase signup response: {resp_json}")
                return resp_json
            except httpx.HTTPStatusError as exc:
                # Only catch and wrap expected HTTP errors
                raise AuthServiceException(exc.response.json().get("msg", "Supabase signup failed"))

    async def login_user(self, email: str, password: str) -> Dict[str, Any]:
        """
        Log in a user with Supabase Auth.
        """
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.supabase_url}/auth/v1/token?grant_type=password",
                    headers={
                        "apikey": self.supabase_key,
                        "Content-Type": "application/json"
                    },
                    json={
                        "email": email,
                        "password": password
                    }
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as exc:
                raise AuthServiceException(exc.response.json().get("msg", "Invalid credentials"))

    async def delete_user(self, supabase_user_id: str) -> None:
        """
        Delete a user from Supabase Auth using the Admin API.
        If the user is not found (404), treat as success (idempotent).
        """
        url = f"{self.supabase_url}/auth/v1/admin/users/{supabase_user_id}"
        headers = {
            "apikey": self.supabase_key,
            "Authorization": f"Bearer {self.supabase_key}"
        }
        async with httpx.AsyncClient() as client:
            try:
                response = await client.delete(url, headers=headers)
                if response.status_code in (200, 204):
                    return
                if response.status_code == 404:
                    # User not found in Supabase, treat as success (idempotent)
                    logging.getLogger(__name__).warning(f"Supabase user not found for deletion: {supabase_user_id}")
                    return
                raise AuthServiceException(f"Failed to delete user from Supabase Auth: {response.text}")
            except httpx.HTTPStatusError as exc:
                raise AuthServiceException(f"Supabase delete user error: {exc.response.text}")
            except Exception as exc:
                raise AuthServiceException(f"Unexpected error deleting user from Supabase Auth: {exc}")

    @staticmethod
    def get_current_user_supabase_id(request: Request) -> str:
        """
        Extracts the supabase_user_id from the JWT in the Authorization header.
        """
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
        token = auth_header.split(" ", 1)[1]
        try:
            payload = jwt.decode(token, settings.SUPABASE_JWT_SECRET, algorithms=["HS256"], audience="authenticated")
            supabase_user_id = payload.get("sub")
            if not supabase_user_id:
                raise HTTPException(status_code=401, detail="supabase_user_id not found in token")
            return supabase_user_id
        except JWTError:
            raise HTTPException(status_code=401, detail="Invalid token")
