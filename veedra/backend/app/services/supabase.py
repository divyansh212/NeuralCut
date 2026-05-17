"""Thin Supabase wrapper used by the backend.

Two clients:
  - `anon`: used for JWT-scoped operations (respects RLS as the user)
  - `admin`: service-role client; used by workers and trusted backend code

If supabase credentials are missing, falls back to raw psycopg against
the dockerized postgres. That keeps local dev frictionless.
"""

from __future__ import annotations
from functools import lru_cache
from typing import Optional

import psycopg
from supabase import create_client, Client

from app.config import get_settings


@lru_cache
def admin_client() -> Optional[Client]:
    s = get_settings()
    if not s.supabase_url or not s.supabase_service_role_key:
        return None
    return create_client(s.supabase_url, s.supabase_service_role_key)


def user_client(access_token: str) -> Optional[Client]:
    """Per-request client scoped to a user's JWT (RLS applies)."""
    s = get_settings()
    if not s.supabase_url or not s.supabase_anon_key:
        return None
    c = create_client(s.supabase_url, s.supabase_anon_key)
    c.auth.set_session(access_token, refresh_token="")
    return c


# ─── Direct SQL fallback (for the dockerized-only path) ──────────────
def pg_conn() -> psycopg.Connection:
    return psycopg.connect(get_settings().supabase_db_url, autocommit=True)
