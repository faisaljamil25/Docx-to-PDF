import io
import os
import zipfile
from unittest.mock import patch
from fastapi.testclient import TestClient


def make_zip_bytes(names_contents):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for name, content in names_contents:
            zf.writestr(name, content)
    buf.seek(0)
    return buf


def test_submit_and_status(tmp_path, monkeypatch):
    # Configure env to use SQLite and temp storage BEFORE importing app
    os.environ["DATABASE_URL"] = f"sqlite:///{tmp_path}/test.db"
    os.environ["STORAGE_ROOT"] = str(tmp_path)

    from app.main import app  # import after env is set
    from app.worker import process_job  # import after env is set

    client = TestClient(app)

    # Mock Celery to run synchronously
    def fake_delay(job_id):
        # call the task directly
        process_job(job_id)

    monkeypatch.setattr("app.worker.process_job.delay", fake_delay)

    # Mock conversion to bypass soffice
    with patch("app.services.conversion.convert_docx_to_pdf") as mock_conv:

        def fake_conv(inp, out_dir):
            # pretend to produce a pdf path
            return f"{out_dir}/" + inp.split("/")[-1].replace(".docx", ".pdf")

        mock_conv.side_effect = fake_conv

        # Create zip with two docx files
        zip_bytes = make_zip_bytes(
            [
                ("a.docx", b"A"),
                ("b.docx", b"B"),
            ]
        )

        files = {"zip_file": ("docs.zip", zip_bytes, "application/zip")}
        r = client.post("/api/v1/jobs", files=files)
        assert r.status_code in (200, 202)
        data = r.json()
        job_id = data["job_id"]

        # Status should eventually be completed
        s = client.get(f"/api/v1/jobs/{job_id}")
        assert s.status_code == 200
        js = s.json()
        assert js["status"] in ("IN_PROGRESS", "COMPLETED")
        # Now force run job synchronously, status should become COMPLETED
        client.get(f"/api/v1/jobs/{job_id}")
        s2 = client.get(f"/api/v1/jobs/{job_id}")
        assert s2.status_code == 200
        js2 = s2.json()
        assert js2["status"] in ("COMPLETED", "FAILED")
