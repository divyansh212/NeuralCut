"""Video understanding: upload a video, ask questions about it.

This is the ViMax / VideoAgent flavor of the platform. The full
implementation needs a frame-sampling + multi-modal LLM pipeline;
this router gives you the upload + ask shape with a stub answer so the
UI works end-to-end.
"""

from __future__ import annotations
import os
import shutil
import tempfile
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException

from app.deps import get_current_user, CurrentUser
from app.services.storage import upload
from app.services.supabase import pg_conn
from app.config import get_settings

router = APIRouter(prefix="/understand", tags=["understand"])


@router.post("/upload")
async def upload_video(
    file: UploadFile = File(...), user: CurrentUser = Depends(get_current_user)
):
    if not (file.content_type or "").startswith("video/"):
        raise HTTPException(400, "Expected video file")
    s = get_settings()
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = tmp.name
    try:
        url = await upload(tmp_path, s.assets_bucket, key_prefix=f"{user.id}/uploads")
        with pg_conn() as conn, conn.cursor() as cur:
            cur.execute(
                "insert into assets (owner_id, kind, storage_path, mime_type, size_bytes) "
                "values (%s, 'video', %s, %s, %s) returning id",
                (str(user.id), url, file.content_type, os.path.getsize(tmp_path)),
            )
            asset_id = cur.fetchone()[0]
        return {"asset_id": str(asset_id), "url": url}
    finally:
        os.unlink(tmp_path)


@router.post("/ask")
async def ask_video(
    asset_id: UUID = Form(...),
    question: str = Form(...),
    user: CurrentUser = Depends(get_current_user),
):
    """Stub: real implementation samples frames + runs them through an MLLM.

    Plug in: ffmpeg frame sampling -> Claude 3.7 vision or Gemini -> answer.
    For now, returns a structured placeholder so the UI can render the
    conversation shape correctly.
    """
    with pg_conn() as conn, conn.cursor() as cur:
        cur.execute(
            "select storage_path from assets where id=%s and owner_id=%s",
            (str(asset_id), str(user.id)),
        )
        row = cur.fetchone()
        if not row:
            raise HTTPException(404, "asset not found")

    return {
        "answer": (
            f"[stubbed video Q&A] Your question: '{question}'. "
            f"Wire app/routers/understand.py:ask_video to a multimodal "
            f"LLM with frame samples to enable real answers."
        ),
        "citations": [
            {"timestamp": 4.2, "frame_url": None},
            {"timestamp": 11.8, "frame_url": None},
        ],
    }
