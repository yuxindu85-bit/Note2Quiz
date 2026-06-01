from pathlib import Path

import pytest

from services.file_parser import FileParseError, extract_text


def test_extract_txt(tmp_path: Path) -> None:
    file_path = tmp_path / "lecture.txt"
    file_path.write_text("  First idea  \n\nSecond idea\n", encoding="utf-8")

    assert extract_text(file_path) == "First idea\nSecond idea"


def test_rejects_empty_txt(tmp_path: Path) -> None:
    file_path = tmp_path / "empty.txt"
    file_path.write_text("   \n", encoding="utf-8")

    with pytest.raises(FileParseError):
        extract_text(file_path)
