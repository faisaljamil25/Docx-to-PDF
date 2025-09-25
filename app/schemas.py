from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel


class JobFileStatus(BaseModel):
    filename: str
    status: str
    error_message: Optional[str] = None


class JobCreateResponse(BaseModel):
    job_id: str
    file_count: int


class JobStatusResponse(BaseModel):
    job_id: str
    status: str
    created_at: datetime
    download_url: Optional[str] = None
    files: List[JobFileStatus]
