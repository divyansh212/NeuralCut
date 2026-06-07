"""Supabase queries via the service key. ALWAYS filtered by user_id so a leaked
or guessed id can't read another user's rows (defense in depth alongside RLS).
"""

from datetime import datetime, timezone
from functools import lru_cache

from supabase import create_client, Client

from .config import settings


@lru_cache(maxsize=1)
def _client() -> Client:
    if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_KEY:
        raise RuntimeError("Supabase not configured (SUPABASE_URL / SUPABASE_SERVICE_KEY).")
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)


def insert_job(user_id: str, prompt: str) -> dict:
    res = (
        _client()
        .table("jobs")
        .insert({"user_id": user_id, "prompt": prompt, "status": "queued"})
        .execute()
    )
    return res.data[0]


def get_job(job_id: str, user_id: str) -> dict:
    res = (
        _client()
        .table("jobs")
        .select("*")
        .eq("id", job_id)
        .eq("user_id", user_id)        # owner scope (alongside RLS)
        .single()
        .execute()
    )
    return res.data


def list_jobs(user_id: str, limit: int = 20) -> list:
    res = (
        _client()
        .table("jobs")
        .select("*")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )
    return res.data or []


def update_job(job_id: str, **fields) -> dict:
    """Called from the worker process (no user in context, so not user-scoped;
    the worker only ever has job ids it was handed by the trusted API)."""
    fields["updated_at"] = datetime.now(timezone.utc).isoformat()
    res = _client().table("jobs").update(fields).eq("id", job_id).execute()
    return res.data[0] if res.data else {"id": job_id, **fields}


def get_job_internal(job_id: str) -> dict:
    """Worker-side read (no user scope — worker is trusted)."""
    res = _client().table("jobs").select("*").eq("id", job_id).single().execute()
    return res.data
