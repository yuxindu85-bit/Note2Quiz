from pathlib import Path

import pytest

from services.file_parser import FileParseError, extract_text
from services.markdown_export import safe_markdown_filename


def test_extract_txt(tmp_path: Path) -> None:
    file_path = tmp_path / "lecture.txt"
    file_path.write_text("  First idea  \n\nSecond idea\n", encoding="utf-8")

    assert extract_text(file_path) == "First idea\nSecond idea"


def test_rejects_empty_txt(tmp_path: Path) -> None:
    file_path = tmp_path / "empty.txt"
    file_path.write_text("   \n", encoding="utf-8")

    with pytest.raises(FileParseError):
        extract_text(file_path)


def test_safe_markdown_filename() -> None:
    assert safe_markdown_filename("Week 1: Cells & Energy") == "Week_1__Cells___Energy.md"
