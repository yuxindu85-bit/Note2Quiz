from pathlib import Path

import pytest

from services.file_parser import FileParseError, extract_text
from services.markdown_export import safe_markdown_filename
from services.ai_client import mock_study_pack


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


def test_mock_study_pack_uses_source_text_variety() -> None:
    text = (
        "Photosynthesis converts light energy into chemical energy. "
        "Chlorophyll captures light inside chloroplasts. "
        "Light reactions produce ATP and NADPH for the Calvin cycle. "
        "The Calvin cycle fixes carbon dioxide into sugars."
    )

    pack = mock_study_pack("biology.txt", text)
    questions = {item["question"] for item in pack["quiz"]}
    flashcard_backs = {item["back"] for item in pack["flashcards"]}

    assert len(pack["quiz"]) == 10
    assert len(pack["flashcards"]) == 20
    assert len(questions) > 1
    assert len(flashcard_backs) > 1
    assert any(term["term"] == "Photosynthesis" for term in pack["key_terms"])
