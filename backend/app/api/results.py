import json
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.storage import storage_client
from app.models import Job, JobStatus, User
from app.api.deps import get_current_user

router = APIRouter(prefix="/api/jobs", tags=["Job Results"])

@router.get("/{job_id}/result")
async def get_job_result(
    job_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Retrieve job execution output payload or MinIO presigned URL."""
    stmt = select(Job).where(Job.id == job_id)
    res = await db.execute(stmt)
    job = res.scalar_one_or_none()

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if job.status != JobStatus.SUCCESS:
        raise HTTPException(
            status_code=400,
            detail=f"Job output unavailable. Current status is '{job.status.value}'."
        )

    if not job.result_location:
        raise HTTPException(status_code=404, detail="No result location found for completed job.")

    # Parse location key (e.g. s3://taskflow-artifacts/ml_results/job_xyz_result.json)
    if job.result_location.startswith("s3://") or "taskflow-artifacts" in job.result_location:
        object_key = job.result_location.split("taskflow-artifacts/")[-1]
        
        # Try fetching object content directly from MinIO
        content_bytes = storage_client.get_object_content(object_key)
        if content_bytes:
            try:
                data = json.loads(content_bytes.decode("utf-8"))
                return JSONResponse(content=data)
            except Exception:
                pass
        
        # Fallback to presigned URL
        presigned_url = storage_client.get_presigned_url(object_key)
        return {"result_location": job.result_location, "download_url": presigned_url}

    return {"result_location": job.result_location}
