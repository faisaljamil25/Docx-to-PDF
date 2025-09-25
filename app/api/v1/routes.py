import shutil
import zipfile
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.core.config import get_settings
from app.db.session import get_db
from app.db.models import Job, JobFile, JobStatus, FileStatus
from app.schemas import JobCreateResponse, JobStatusResponse, JobFileStatus

router = APIRouter()
settings = get_settings()


@router.post("/jobs", response_model=JobCreateResponse, status_code=202)
async def create_job(zip_file: UploadFile = File(...), db: Session = Depends(get_db)):
    # Basic validation
    if not zip_file.filename or not zip_file.filename.lower().endswith(".zip"):
        raise HTTPException(
            status_code=400, detail="Upload must be a .zip file containing DOCX files"
        )

    job = Job(status=JobStatus.PENDING)
    db.add(job)
    db.commit()
    db.refresh(job)

    job_dir = Path(settings.STORAGE_INPUT) / str(job.id)
    job_dir.mkdir(parents=True, exist_ok=True)

    zip_path = job_dir / "upload.zip"
    with open(zip_path, "wb") as f:
        shutil.copyfileobj(zip_file.file, f)

    # Extract
    saved_files = 0
    with zipfile.ZipFile(zip_path, "r") as zf:
        members = zf.namelist()
        docx_members = [m for m in members if m.lower().endswith(".docx")]
        if not docx_members:
            raise HTTPException(status_code=400, detail="Zip contains no .docx files")
        for m in docx_members:
            # prevent zip slip
            member_path = Path(m)
            if member_path.is_absolute() or ".." in member_path.parts:
                continue
            target = job_dir / member_path.name
            with zf.open(m) as src, open(target, "wb") as dst:
                shutil.copyfileobj(src, dst)
            job_file = JobFile(
                job_id=job.id,
                original_filename=member_path.name,
                input_path=str(target),
                status=FileStatus.PENDING,
            )
            db.add(job_file)
            saved_files += 1
    job.total_files = saved_files
    db.commit()

    # Enqueue background processing via Celery
    try:
        from app.worker import process_job

        process_job.delay(str(job.id))  # type: ignore[attr-defined]
    except Exception as e:
        # If queueing fails, mark job failed
        job.status = JobStatus.FAILED
        db.commit()
        raise HTTPException(status_code=500, detail=f"Failed to enqueue job: {e}")

    return JobCreateResponse(job_id=job.id, file_count=job.total_files)


@router.get("/jobs/{job_id}", response_model=JobStatusResponse)
def get_job_status(job_id: str, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    files = db.query(JobFile).filter(JobFile.job_id == job.id).all()
    file_statuses = [
        JobFileStatus(
            filename=f.original_filename,
            status=f.status.value,
            error_message=f.error_message,
        )
        for f in files
    ]

    download_url = None
    if job.status == JobStatus.COMPLETED and bool(job.archive_path):
        download_url = f"{settings.API_V1_PREFIX}/jobs/{job.id}/download"

    return JobStatusResponse(
        job_id=job.id,
        status=job.status.value,
        created_at=job.created_at,
        download_url=download_url,
        files=file_statuses,
    )


@router.get("/jobs/{job_id}/download")
def download_job_archive(job_id: str, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if job.status != JobStatus.COMPLETED or not job.archive_path:
        raise HTTPException(
            status_code=400, detail="Job not completed or archive not available"
        )

    path = Path(job.archive_path)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Archive not found on disk")

    return FileResponse(path, media_type="application/zip", filename=f"{job.id}.zip")
