import importlib
from pathlib import Path

from fastapi.testclient import TestClient


def test_upload_generate_list_and_export(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("NOTE2QUIZ_DB_PATH", str(tmp_path / "note2quiz.db"))
    monkeypatch.setenv("NOTE2QUIZ_UPLOAD_DIR", str(tmp_path / "uploads"))
    monkeypatch.delenv("AI_API_KEY", raising=False)

    main = importlib.import_module("main")
    main.UPLOAD_DIR = tmp_path / "uploads"
    main.setup_app_storage()

    client = TestClient(main.app)
    upload_response = client.post(
        "/api/upload",
        files={"file": ("lecture.txt", b"Photosynthesis converts light into chemical energy.", "text/plain")},
    )

    assert upload_response.status_code == 200
    file_id = upload_response.json()["file_id"]

    generate_response = client.post(f"/api/generate/{file_id}")
    assert generate_response.status_code == 200
    pack = generate_response.json()
    assert pack["summary"].startswith("Demo summary")
    assert len(pack["quiz"]) == 10
    assert len(pack["flashcards"]) == 20

    duplicate_response = client.post(f"/api/generate/{file_id}")
    assert duplicate_response.status_code == 200
    assert duplicate_response.json()["id"] == pack["id"]

    list_response = client.get("/api/packs")
    assert list_response.status_code == 200
    assert list_response.json()["packs"][0]["id"] == pack["id"]

    export_response = client.get(f"/api/export/{pack['id']}")
    assert export_response.status_code == 200
    assert "# lecture.txt" in export_response.text


def test_upload_rejects_unsupported_file(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("NOTE2QUIZ_DB_PATH", str(tmp_path / "note2quiz.db"))
    monkeypatch.setenv("NOTE2QUIZ_UPLOAD_DIR", str(tmp_path / "uploads"))

    main = importlib.import_module("main")
    main.UPLOAD_DIR = tmp_path / "uploads"
    main.setup_app_storage()

    client = TestClient(main.app)
    response = client.post(
        "/api/upload",
        files={"file": ("lecture.csv", b"not supported", "text/csv")},
    )

    assert response.status_code == 400
