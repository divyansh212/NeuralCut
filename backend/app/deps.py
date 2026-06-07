"""Authentication — real Supabase JWT verification, NO bypass.

The cardinal rule from the skill: there is no dev mode that accepts arbitrary
identities. Every protected request carries a Supabase-issued JWT and we verify
its signature. Mocking *generation* is fine; mocking *identity* is never fine,
because that shortcut becomes a public backdoor the instant the service is
reachable. If the JWT secret is missing we fail loudly at startup (config check)
rather than silently running insecure.
"""

import jwt
from fastapi import HTTPException, Header

from .config import settings


def get_current_user(authorization: str = Header(None)) -> dict:
    if not settings.SUPABASE_JWT_SECRET:
        # Misconfiguration: refuse rather than fall back to an insecure mode.
        raise HTTPException(500, "Server auth not configured (SUPABASE_JWT_SECRET missing)")

    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "Missing bearer token")

    token = authorization.split(" ", 1)[1]
    try:
        payload = jwt.decode(
            token,
            settings.SUPABASE_JWT_SECRET,
            algorithms=["HS256"],
            audience="authenticated",
        )
    except jwt.PyJWTError:
        raise HTTPException(401, "Invalid or expired token")

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(401, "Token missing subject")
    return {"id": user_id, "email": payload.get("email")}
