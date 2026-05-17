"""Object storage abstraction.

Prefers Supabase Storage; falls back to local disk + a static-file URL
when service credentials are absent. Either way the orchestrator code is
identical.
"""

from __future__ import annotations
import os
import shutil
import uuid
from pathlib import Path

from app.config import get_settings
from app.services.supabase import admin_client


def _ext_for(local_path: str) -> str:
    return os.path.splitext(local_path)[1].lstrip(".") or "bin"


async def upload(local_path: str, bucket: str, key_prefix: str = "") -> str:
    """Uploads a file and returns a URL the frontend can fetch."""
    s = get_settings()
    key = f"{key_prefix.rstrip('/')}/{uuid.uuid4().hex}.{_ext_for(local_path)}".lstrip("/")

    sb = admin_client()
    if sb is not None:
        with open(local_path, "rb") as f:
            sb.storage.from_(bucket).upload(
                path=key,
                file=f.read(),
                file_options={"content-type": _mime(local_path), "upsert": "false"},
            )
        # Public for the renders bucket; signed for assets
        if bucket == s.renders_bucket:
            return sb.storage.from_(bucket).get_public_url(key)
        return sb.storage.from_(bucket).create_signed_url(key, 3600)["signedURL"]

    # Local fallback: copy to /tmp/veedra/<bucket>/<key>, serve via /static
    dest_dir = Path(s.local_storage_dir) / bucket
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / key.replace("/", "_")
    shutil.copy2(local_path, dest)
    return f"/static/{bucket}/{dest.name}"


def _mime(path: str) -> str:
    e = path.lower().rsplit(".", 1)[-1]
    return {
        "png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg",
        "webp": "image/webp", "mp4": "video/mp4", "mp3": "audio/mpeg",
        "wav": "audio/wav",
    }.get(e, "application/octet-stream")
