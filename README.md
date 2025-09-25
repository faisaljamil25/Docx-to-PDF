# Docx-to-PDF Conversion Service

A robust, scalable, asynchronous FastAPI microservice that converts batches of DOCX files into PDFs using background workers and generates a final zip archive for download.

## Architecture

- FastAPI service exposes REST API for job submission, status, and download.
- PostgreSQL stores job and file statuses.
- Redis is used as the Celery broker and result backend.
- Celery worker picks up jobs, converts DOCX to PDF using LibreOffice (soffice), and archives results.
- Docker volumes share input/output/archive directories between API and worker.

Shared directories within the containers:
- `/data/inputs/<job_id>`: extracted docx files
- `/data/outputs/<job_id>`: generated PDFs
- `/data/archives/<job_id>.zip`: final zip

## Run locally with Docker

1. Ensure Docker is installed.
2. Build and start the stack:

```sh
docker compose up --build
```

3. Open Swagger UI: http://localhost:8000/docs

## API

- POST `/api/v1/jobs` (multipart/form-data with "zip_file"): Submit a zip of DOCX files. Returns 202 with `job_id` and `file_count`.
- GET `/api/v1/jobs/{job_id}`: Check job status and per-file results. When completed, includes `download_url`.
- GET `/api/v1/jobs/{job_id}/download`: Download the final zip archive.

## Configuration

Environment variables (see `.env.example`):
- STORAGE_ROOT: Root shared volume path (default `/data`)
- POSTGRES_*: Database connection settings
- REDIS_*: Redis connection settings
- SOFFICE_BIN: LibreOffice binary (default `soffice`)

## Development notes

- SQLAlchemy models are auto-created on API start; for production, manage migrations (e.g., Alembic).
- Single-file conversion failures don't stop the whole job; they are captured per-file.
- Zip slip protected extraction and path checks included.

## Tests

TBD: add pytest tests for utils and API lifecycle with mocked conversion.
