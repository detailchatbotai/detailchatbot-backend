import httpx
import logging
from typing import Any, Dict, Optional
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
