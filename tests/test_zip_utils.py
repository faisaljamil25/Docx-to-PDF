from app.utils.zip_utils import zip_directory
from pathlib import Path


def test_zip_directory_creates_archive(tmp_path: Path):
    f1 = tmp_path / "a.pdf"
    f2 = tmp_path / "b.pdf"
    f1.write_text("x")
    f2.write_text("y")
    archive = tmp_path / "out.zip"

    result = zip_directory([str(f1), str(f2)], str(archive))

    assert Path(result).exists()
