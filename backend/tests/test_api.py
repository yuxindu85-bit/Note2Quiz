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

    regenerated_response = client.post(f"/api/generate/{file_id}?force=true")
    assert regenerated_response.status_code == 200
    assert regenerated_response.json()["id"] != pack["id"]

    list_response = client.get("/api/packs")
    assert list_response.status_code == 200
    assert list_response.json()["packs"][0]["id"] == regenerated_response.json()["id"]

    export_response = client.get(f"/api/export/{regenerated_response.json()['id']}")
    assert export_response.status_code == 200
    assert "# lecture.txt" in export_response.text


def test_generate_accepts_study_options(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("NOTE2QUIZ_DB_PATH", str(tmp_path / "note2quiz.db"))
    monkeypatch.setenv("NOTE2QUIZ_UPLOAD_DIR", str(tmp_path / "uploads"))
    monkeypatch.delenv("AI_API_KEY", raising=False)

    main = importlib.import_module("main")
    main.UPLOAD_DIR = tmp_path / "uploads"
    main.setup_app_storage()

    client = TestClient(main.app)
    upload_response = client.post(
        "/api/upload",
        files={
            "file": (
                "economics.txt",
                (
                    b"Pricing strategy uses consumer data to estimate willingness to pay. "
                    b"Companies compare market demand, discounts, coupons, airline tickets, and competition."
                ),
                "text/plain",
            )
        },
    )
    file_id = upload_response.json()["file_id"]

    response = client.post(
        f"/api/generate/{file_id}",
        json={"key_terms_count": 5, "quiz_order": "random", "language": "auto", "translation_language": "chinese"},
    )

    assert response.status_code == 200
    pack = response.json()
    assert pack["key_terms_count"] == 5
    assert pack["quiz_order"] == "random"
    assert pack["language"] == "english"
    assert pack["translation_language"] == "chinese"
    assert len(pack["key_terms"]) == 5
    assert "Demo translation preview" in pack["translation_text"]

    export_response = client.get(f"/api/export/{pack['id']}")
    assert export_response.status_code == 200
    assert "## Translation (Chinese)" in export_response.text


def test_exam_wrong_answers_and_study_plan(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("NOTE2QUIZ_DB_PATH", str(tmp_path / "note2quiz.db"))
    monkeypatch.setenv("NOTE2QUIZ_UPLOAD_DIR", str(tmp_path / "uploads"))
    monkeypatch.delenv("AI_API_KEY", raising=False)

    main = importlib.import_module("main")
    main.UPLOAD_DIR = tmp_path / "uploads"
    main.setup_app_storage()

    client = TestClient(main.app)
    upload_response = client.post(
        "/api/upload",
        files={
            "file": (
                "biology.txt",
                b"Photosynthesis converts light energy into chemical energy. Chlorophyll captures light.",
                "text/plain",
            )
        },
    )
    file_id = upload_response.json()["file_id"]
    pack = client.post(f"/api/generate/{file_id}").json()

    start_response = client.post(f"/api/packs/{pack['id']}/exam/start")
    assert start_response.status_code == 200
    exam = start_response.json()
    assert len(exam["questions"]) == 10

    wrong_answer = "Definitely wrong"
    submit_response = client.post(
        f"/api/packs/{pack['id']}/exam/submit",
        json={
            "attempt_id": exam["attempt_id"],
            "duration_seconds": 42,
            "answers": [{"question_index": 0, "answer": wrong_answer}],
        },
    )
    assert submit_response.status_code == 200
    result = submit_response.json()
    assert result["total_questions"] == 10
    assert result["score"] < result["total_questions"]

    attempts_response = client.get("/api/exam-attempts")
    assert attempts_response.status_code == 200
    assert attempts_response.json()["attempts"][0]["id"] == exam["attempt_id"]

    wrong_response = client.get("/api/wrong-answers")
    assert wrong_response.status_code == 200
    wrong_answers = wrong_response.json()["wrong_answers"]
    assert wrong_answers
    assert wrong_answers[0]["user_answer"] == wrong_answer

    plan_response = client.post(f"/api/packs/{pack['id']}/study-plan", json={"duration_days": 5})
    assert plan_response.status_code == 200
    plan = plan_response.json()
    assert plan["duration_days"] == 5
    assert len(plan["plan"]) == 5


def test_health_check_reports_demo_mode(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("NOTE2QUIZ_DB_PATH", str(tmp_path / "note2quiz.db"))
    monkeypatch.setenv("NOTE2QUIZ_UPLOAD_DIR", str(tmp_path / "uploads"))
    monkeypatch.delenv("AI_API_KEY", raising=False)

    main = importlib.import_module("main")
    main.UPLOAD_DIR = tmp_path / "uploads"
    main.setup_app_storage()

    client = TestClient(main.app)
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["demo_mode"] is True


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
