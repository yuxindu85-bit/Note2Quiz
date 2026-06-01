import json
import os
import shutil
import uuid
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
from pathlib import Path

import httpx
from dotenv import load_dotenv
from fastapi import Body, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse

from database import get_connection, init_db, row_to_pack
from schemas import (
    ExamAttemptListResponse,
    ExamStartResponse,
    ExamSubmitRequest,
    ExamSubmitResponse,
    GenerateOptions,
    HealthResponse,
    StudyPack,
    StudyPackListResponse,
    StudyPlanRequest,
    StudyPlanResponse,
    UploadResponse,
    WrongAnswerListResponse,
)
from services.ai_client import generate_study_pack
from services.file_parser import SUPPORTED_EXTENSIONS, FileParseError, extract_text
from services.markdown_export import pack_to_markdown, safe_markdown_filename
from services.study_plan import mock_study_plan


BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")
load_dotenv(BASE_DIR.parent / ".env")
UPLOAD_DIR = Path(os.getenv("NOTE2QUIZ_UPLOAD_DIR", BASE_DIR / "uploads"))
if not UPLOAD_DIR.is_absolute():
    UPLOAD_DIR = BASE_DIR.parent / UPLOAD_DIR


def setup_app_storage() -> None:
    init_db()
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    setup_app_storage()
    yield


app = FastAPI(title="Note2Quiz API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    try:
        with get_connection() as conn:
            conn.execute("SELECT 1").fetchone()
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Database is not available.") from exc

    return HealthResponse(
        status="ok",
        database="sqlite",
        demo_mode=not bool(os.getenv("AI_API_KEY")),
        ai_model=os.getenv("AI_MODEL", "gpt-4o-mini"),
    )


@app.post("/api/upload", response_model=UploadResponse)
async def upload_file(file: UploadFile = File(...)) -> UploadResponse:
    extension = Path(file.filename or "").suffix.lower()
    if extension not in SUPPORTED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Upload a PDF, DOCX, PPTX, or TXT file.")

    file_id = str(uuid.uuid4())
    safe_name = Path(file.filename or f"upload{extension}").name
    stored_path = UPLOAD_DIR / f"{file_id}_{safe_name}"

    try:
        UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        with stored_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        extracted_text = extract_text(stored_path)
    except FileParseError as exc:
        stored_path.unlink(missing_ok=True)
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        stored_path.unlink(missing_ok=True)
        raise HTTPException(status_code=500, detail="Could not process uploaded file.") from exc

    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO uploaded_files (id, original_filename, stored_path, extracted_text)
            VALUES (?, ?, ?, ?)
            """,
            (file_id, safe_name, str(stored_path), extracted_text),
        )

    return UploadResponse(
        file_id=file_id,
        filename=safe_name,
        text_length=len(extracted_text),
        preview=extracted_text[:500],
    )


@app.post("/api/generate/{file_id}", response_model=StudyPack)
async def generate_pack(
    file_id: str,
    options: GenerateOptions = Body(default_factory=GenerateOptions),
    force: bool = False,
) -> StudyPack:
    force_generation = force or options.force
    with get_connection() as conn:
        file_row = conn.execute("SELECT * FROM uploaded_files WHERE id = ?", (file_id,)).fetchone()
        existing_pack = conn.execute("SELECT * FROM study_packs WHERE file_id = ?", (file_id,)).fetchone()

    if file_row is None:
        raise HTTPException(status_code=404, detail="Uploaded file not found.")
    if existing_pack is not None and not force_generation:
        return StudyPack(**row_to_pack(existing_pack))

    try:
        generated = await generate_study_pack(
            file_row["extracted_text"],
            file_row["original_filename"],
            quiz_count=options.quiz_count,
            key_terms_count=options.key_terms_count,
            quiz_order=options.quiz_order,
            language=options.language,
            translation_language=options.translation_language,
        )
    except httpx.HTTPStatusError as exc:
        detail = exc.response.text[:400] if exc.response is not None else "AI provider error."
        raise HTTPException(status_code=502, detail=f"AI provider error: {detail}") from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Could not generate study pack.") from exc

    pack_id = str(uuid.uuid4())
    with get_connection() as conn:
        if force_generation:
            conn.execute("DELETE FROM study_packs WHERE file_id = ?", (file_id,))
        conn.execute(
            """
            INSERT INTO study_packs
            (
                id, file_id, title, summary, quiz_json, flashcards_json, key_terms_json,
                original_text, translation_text, language, translation_language, quiz_count, key_terms_count, quiz_order
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                pack_id,
                file_id,
                generated["title"],
                generated["summary"],
                json.dumps(generated["quiz"]),
                json.dumps(generated["flashcards"]),
                json.dumps(generated["key_terms"]),
                generated["original_text"],
                generated["translation_text"],
                generated["language"],
                generated["translation_language"],
                generated["quiz_count"],
                generated["key_terms_count"],
                generated["quiz_order"],
            ),
        )
        row = conn.execute("SELECT * FROM study_packs WHERE id = ?", (pack_id,)).fetchone()

    return StudyPack(**row_to_pack(row))


@app.get("/api/packs", response_model=StudyPackListResponse)
def list_packs() -> StudyPackListResponse:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT id, file_id, title, summary, created_at
            FROM study_packs
            ORDER BY created_at DESC
            """
        ).fetchall()
    return StudyPackListResponse(packs=[dict(row) for row in rows])


@app.get("/api/packs/{pack_id}", response_model=StudyPack)
def get_pack(pack_id: str) -> StudyPack:
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM study_packs WHERE id = ?", (pack_id,)).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Study pack not found.")
    return StudyPack(**row_to_pack(row))


@app.post("/api/packs/{pack_id}/exam/start", response_model=ExamStartResponse)
def start_exam(pack_id: str) -> ExamStartResponse:
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM study_packs WHERE id = ?", (pack_id,)).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="Study pack not found.")

        pack = row_to_pack(row)
        questions = pack["quiz"]
        if not questions:
            raise HTTPException(status_code=422, detail="This study pack has no quiz questions.")

        attempt_id = str(uuid.uuid4())
        conn.execute(
            """
            INSERT INTO exam_attempts (id, pack_id, total_questions, status)
            VALUES (?, ?, ?, 'in_progress')
            """,
            (attempt_id, pack_id, len(questions)),
        )

    return ExamStartResponse(
        attempt_id=attempt_id,
        pack_id=pack_id,
        title=pack["title"],
        questions=questions,
    )


@app.post("/api/packs/{pack_id}/exam/submit", response_model=ExamSubmitResponse)
def submit_exam(pack_id: str, payload: ExamSubmitRequest) -> ExamSubmitResponse:
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM study_packs WHERE id = ?", (pack_id,)).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="Study pack not found.")

        pack = row_to_pack(row)
        questions = pack["quiz"]
        answers_by_index = {answer.question_index: answer.answer for answer in payload.answers}
        review: list[dict] = []
        wrong_rows: list[tuple[str, str, str, str, str, str]] = []

        for index, question in enumerate(questions):
            correct_answer = str(question.get("answer", ""))
            user_answer = str(answers_by_index.get(index, ""))
            is_correct = user_answer == correct_answer
            explanation = _question_explanation(question, correct_answer)
            review_item = {
                "question_index": index,
                "question": question.get("question", ""),
                "choices": question.get("choices", []),
                "user_answer": user_answer,
                "correct_answer": correct_answer,
                "is_correct": is_correct,
                "explanation": explanation,
            }
            review.append(review_item)
            if not is_correct:
                wrong_rows.append(
                    (
                        str(uuid.uuid4()),
                        "",
                        pack_id,
                        review_item["question"],
                        user_answer or "No answer",
                        correct_answer,
                        explanation,
                    )
                )

        score = sum(1 for item in review if item["is_correct"])
        attempt_id = payload.attempt_id or str(uuid.uuid4())
        existing_attempt = conn.execute("SELECT id FROM exam_attempts WHERE id = ?", (attempt_id,)).fetchone()
        if existing_attempt is None:
            conn.execute(
                """
                INSERT INTO exam_attempts (id, pack_id, total_questions, status)
                VALUES (?, ?, ?, 'in_progress')
                """,
                (attempt_id, pack_id, len(questions)),
            )

        conn.execute(
            """
            UPDATE exam_attempts
            SET score = ?, total_questions = ?, duration_seconds = ?, answers_json = ?,
                review_json = ?, status = 'completed', completed_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (
                score,
                len(questions),
                payload.duration_seconds,
                json.dumps([answer.model_dump() for answer in payload.answers]),
                json.dumps(review),
                attempt_id,
            ),
        )
        conn.execute("DELETE FROM wrong_answers WHERE attempt_id = ?", (attempt_id,))
        for wrong_row in wrong_rows:
            conn.execute(
                """
                INSERT INTO wrong_answers
                (id, attempt_id, pack_id, question, user_answer, correct_answer, explanation)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (wrong_row[0], attempt_id, *wrong_row[2:]),
            )

    return ExamSubmitResponse(
        attempt_id=attempt_id,
        pack_id=pack_id,
        score=score,
        total_questions=len(questions),
        review=review,
    )


@app.get("/api/exam-attempts", response_model=ExamAttemptListResponse)
def list_exam_attempts() -> ExamAttemptListResponse:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT exam_attempts.id, exam_attempts.pack_id, study_packs.title,
                   exam_attempts.score, exam_attempts.total_questions,
                   exam_attempts.duration_seconds, exam_attempts.status,
                   exam_attempts.created_at, exam_attempts.completed_at
            FROM exam_attempts
            JOIN study_packs ON study_packs.id = exam_attempts.pack_id
            ORDER BY exam_attempts.created_at DESC
            """
        ).fetchall()
    return ExamAttemptListResponse(attempts=[dict(row) for row in rows])


@app.get("/api/wrong-answers", response_model=WrongAnswerListResponse)
def list_wrong_answers() -> WrongAnswerListResponse:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT wrong_answers.id, wrong_answers.attempt_id, wrong_answers.pack_id,
                   study_packs.title AS pack_title, wrong_answers.question,
                   wrong_answers.user_answer, wrong_answers.correct_answer,
                   wrong_answers.explanation, wrong_answers.created_at
            FROM wrong_answers
            JOIN study_packs ON study_packs.id = wrong_answers.pack_id
            ORDER BY wrong_answers.created_at DESC
            """
        ).fetchall()
    return WrongAnswerListResponse(wrong_answers=[dict(row) for row in rows])


@app.post("/api/packs/{pack_id}/study-plan", response_model=StudyPlanResponse)
def create_study_plan(pack_id: str, payload: StudyPlanRequest) -> StudyPlanResponse:
    if payload.duration_days not in {3, 5, 7}:
        raise HTTPException(status_code=422, detail="Choose a 3-day, 5-day, or 7-day study plan.")

    with get_connection() as conn:
        row = conn.execute("SELECT * FROM study_packs WHERE id = ?", (pack_id,)).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="Study pack not found.")
        existing = conn.execute(
            "SELECT * FROM study_plans WHERE pack_id = ? AND duration_days = ?",
            (pack_id, payload.duration_days),
        ).fetchone()
        if existing is not None:
            return StudyPlanResponse(
                id=existing["id"],
                pack_id=existing["pack_id"],
                duration_days=existing["duration_days"],
                plan=json.loads(existing["plan_json"]),
                created_at=existing["created_at"],
            )

        pack = row_to_pack(row)
        plan = mock_study_plan(pack, payload.duration_days)
        plan_id = str(uuid.uuid4())
        conn.execute(
            """
            INSERT INTO study_plans (id, pack_id, duration_days, plan_json)
            VALUES (?, ?, ?, ?)
            """,
            (plan_id, pack_id, payload.duration_days, json.dumps(plan)),
        )
        plan_row = conn.execute("SELECT * FROM study_plans WHERE id = ?", (plan_id,)).fetchone()

    return StudyPlanResponse(
        id=plan_row["id"],
        pack_id=plan_row["pack_id"],
        duration_days=plan_row["duration_days"],
        plan=json.loads(plan_row["plan_json"]),
        created_at=plan_row["created_at"],
    )


@app.get("/api/export/{pack_id}", response_class=PlainTextResponse)
def export_pack(pack_id: str) -> PlainTextResponse:
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM study_packs WHERE id = ?", (pack_id,)).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Study pack not found.")

    markdown = pack_to_markdown(row_to_pack(row))
    filename = safe_markdown_filename(row["title"])
    return PlainTextResponse(
        markdown,
        media_type="text/markdown",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


def _question_explanation(question: dict, correct_answer: str) -> str:
    explanation = question.get("explanation")
    if explanation:
        return str(explanation)
    return f"The correct answer is supported by the study pack: {correct_answer}"
