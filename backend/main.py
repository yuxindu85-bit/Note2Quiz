import json
import os
import shutil
import uuid
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
from pathlib import Path

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse

from database import get_connection, init_db, row_to_pack
from schemas import HealthResponse, StudyPack, StudyPackListResponse, UploadResponse
from services.ai_client import generate_study_pack
from services.file_parser import SUPPORTED_EXTENSIONS, FileParseError, extract_text
from services.markdown_export import pack_to_markdown, safe_markdown_filename


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
async def generate_pack(file_id: str, force: bool = False) -> StudyPack:
    with get_connection() as conn:
        file_row = conn.execute("SELECT * FROM uploaded_files WHERE id = ?", (file_id,)).fetchone()
        existing_pack = conn.execute("SELECT * FROM study_packs WHERE file_id = ?", (file_id,)).fetchone()

    if file_row is None:
        raise HTTPException(status_code=404, detail="Uploaded file not found.")
    if existing_pack is not None and not force:
        return StudyPack(**row_to_pack(existing_pack))

    try:
        generated = await generate_study_pack(file_row["extracted_text"], file_row["original_filename"])
    except httpx.HTTPStatusError as exc:
        detail = exc.response.text[:400] if exc.response is not None else "AI provider error."
        raise HTTPException(status_code=502, detail=f"AI provider error: {detail}") from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Could not generate study pack.") from exc

    pack_id = str(uuid.uuid4())
    with get_connection() as conn:
        if force:
            conn.execute("DELETE FROM study_packs WHERE file_id = ?", (file_id,))
        conn.execute(
            """
            INSERT INTO study_packs
            (id, file_id, title, summary, quiz_json, flashcards_json, key_terms_json, original_text)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
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
