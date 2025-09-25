import subprocess
from pathlib import Path
from typing import Optional
from app.core.config import get_settings

settings = get_settings()


def convert_docx_to_pdf(input_path: str, output_dir: str) -> Optional[str]:
    """
    Uses LibreOffice (soffice) headless to convert DOCX to PDF.
    Returns the output PDF path on success, or None on failure.
    """
    input_p = Path(input_path)
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    try:
        # soffice --headless --convert-to pdf --outdir <out_dir> <input>
        result = subprocess.run(
            [
                settings.SOFFICE_BIN,
                "--headless",
                "--convert-to",
                "pdf",
                "--outdir",
                str(out_dir),
                str(input_p),
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            text=True,
        )
        if result.returncode != 0:
            return None
        # LibreOffice names output as <name>.pdf in out_dir
        pdf_name = input_p.with_suffix(".pdf").name
        pdf_path = out_dir / pdf_name
        return str(pdf_path) if pdf_path.exists() else None
    except Exception:
        return None
