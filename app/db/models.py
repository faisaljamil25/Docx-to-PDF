import enum
import uuid
from datetime import datetime
from sqlalchemy import String, Enum, DateTime, ForeignKey, Integer, Text
from sqlalchemy.orm import relationship, Mapped, mapped_column
from typing import Optional, List
from app.db.session import Base


class JobStatus(str, enum.Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class FileStatus(str, enum.Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    status: Mapped[JobStatus] = mapped_column(
        Enum(JobStatus), nullable=False, default=JobStatus.PENDING
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
    total_files: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    completed_files: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    failed_files: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    archive_path: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    files: Mapped[List["JobFile"]] = relationship(
        "JobFile", back_populates="job", cascade="all, delete-orphan"
    )


class JobFile(Base):
    __tablename__ = "job_files"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    job_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False
    )
    original_filename: Mapped[str] = mapped_column(String, nullable=False)
    input_path: Mapped[str] = mapped_column(String, nullable=False)
    output_path: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    status: Mapped[FileStatus] = mapped_column(
        Enum(FileStatus), nullable=False, default=FileStatus.PENDING
    )
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    job: Mapped[Job] = relationship("Job", back_populates="files")
