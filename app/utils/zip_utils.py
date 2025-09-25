import zipfile
from pathlib import Path
from typing import List


def zip_directory(files: List[str], archive_path: str) -> str:
    Path(archive_path).parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archive_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for file_path in files:
            p = Path(file_path)
            if p.exists():
                zf.write(p, arcname=p.name)
    return archive_path
