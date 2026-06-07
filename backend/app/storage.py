"""Upload finished renders to Supabase Storage under renders/{user_id}/{job_id}.mp4
so the owner-write storage policy (folder-prefix based) is satisfied.
"""

import os

from .config import settings
from .db import _client, get_job_internal


def upload_render(job_id: str, local_path: str) -> str:
    job = get_job_internal(job_id)
    user_id = job["user_id"]
    key = f"{user_id}/{job_id}.mp4"

    with open(local_path, "rb") as f:
        data = f.read()

    bucket = _client().storage.from_(settings.STORAGE_BUCKET)
    # upsert so re-runs of the same job overwrite cleanly
    bucket.upload(
        key,
        data,
        {"content-type": "video/mp4", "x-upsert": "true"},
    )
    return bucket.get_public_url(key)
