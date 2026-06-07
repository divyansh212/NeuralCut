from fastapi import APIRouter, Depends
from pydantic import BaseModel

from ..db import insert_job, get_job, list_jobs
from ..deps import get_current_user
from ..worker import run_pipeline

router = APIRouter()


class CreateJob(BaseModel):
    prompt: str


@router.post("/jobs")
def create_job(body: CreateJob, user=Depends(get_current_user)):
    job = insert_job(user_id=user["id"], prompt=body.prompt)   # status=queued
    run_pipeline.delay(job["id"])                              # enqueue on Redis
    return {"job_id": job["id"], "status": "queued"}


@router.get("/jobs")
def my_jobs(user=Depends(get_current_user)):
    return list_jobs(user_id=user["id"])


@router.get("/jobs/{job_id}")
def job_status(job_id: str, user=Depends(get_current_user)):
    return get_job(job_id, user_id=user["id"])   # scoped to owner
