"""FastAPI dependencies. Pulls the Supabase user from the bearer token."""

from __future__ import annotations
from typing import Optional
from uuid import UUID

from fastapi import Header, HTTPException, status

from app.services.supabase import admin_client


class CurrentUser:
    def __init__(self, id: UUID, email: str, access_token: str):
        self.id = id
        self.email = email
        self.access_token = access_token


async def get_current_user(
    authorization: Optional[str] = Header(default=None),
) -> CurrentUser:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Missing bearer token")
    token = authorization.split(" ", 1)[1]

    sb = admin_client()
    if sb is None:
        # Local dev without Supabase: trust the token as a uuid prefix.
        # Replace with proper JWT verification when you wire up hosted Supabase.
        try:
            uid = UUID(token[:36])
        except Exception:
            raise HTTPException(401, "Local dev: token must be a uuid")
        return CurrentUser(id=uid, email=f"{uid}@local.dev", access_token=token)

    # Hosted Supabase: verify by calling auth.getUser
    res = sb.auth.get_user(token)
    user = getattr(res, "user", None)
    if not user:
        raise HTTPException(401, "Invalid token")
    return CurrentUser(id=UUID(user.id), email=user.email or "", access_token=token)
