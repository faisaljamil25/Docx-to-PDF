from celery import Celery
from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.core.config import get_settings
from app.db.session import SessionLocal
from app.db.models import Job, JobFile, JobStatus, FileStatus
from app.services import conversion
from app.utils.zip_utils import zip_directory
from pathlib import Path

settings = get_settings()

celery_app = Celery(
    settings.APP_NAME,
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)


@celery_app.task
def process_job(job_id: str):
    db: Session = SessionLocal()
    try:
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            return
        job.status = JobStatus.IN_PROGRESS
        db.commit()

        output_dir = Path(settings.STORAGE_OUTPUT) / str(job.id)
        output_dir.mkdir(parents=True, exist_ok=True)

        files = db.query(JobFile).filter(JobFile.job_id == job.id).all()
        for f in files:
            f.status = FileStatus.IN_PROGRESS
            db.commit()
            pdf_path = conversion.convert_docx_to_pdf(f.input_path, str(output_dir))
            if pdf_path:
                f.status = FileStatus.COMPLETED
                f.output_path = pdf_path
                job.completed_files += 1
            else:
                f.status = FileStatus.FAILED
                f.error_message = "Conversion failed"
                job.failed_files += 1
            db.commit()

        # Finalize: zip all completed PDFs
        completed = (
            db.query(JobFile)
            .filter(
                and_(JobFile.job_id == job.id, JobFile.status == FileStatus.COMPLETED)
            )
            .all()
        )
        failed_count = (
            db.query(JobFile)
            .filter(and_(JobFile.job_id == job.id, JobFile.status == FileStatus.FAILED))
            .count()
        )
        completed_count = len(completed)
        job.completed_files = completed_count
        job.failed_files = failed_count
        pdfs = [f.output_path for f in completed if f.output_path]
        archive_path = Path(settings.STORAGE_ARCHIVES) / f"{job.id}.zip"
        zip_directory(pdfs, str(archive_path))
        job.archive_path = str(archive_path)

        # Set final status
        if job.total_files > 0 and (completed_count + failed_count == job.total_files):
            # If at least one succeeded, mark COMPLETED; else FAILED
            job.status = (
                JobStatus.COMPLETED if completed_count > 0 else JobStatus.FAILED
            )
        elif job.total_files == 0:
            # Shouldn't usually happen (API prevents), but keep safe default
            job.status = JobStatus.FAILED
        else:
            job.status = JobStatus.FAILED
        db.commit()
    finally:
        db.close()
