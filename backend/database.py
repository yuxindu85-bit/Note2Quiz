import json
import os
import sqlite3
from pathlib import Path
from typing import Any


BASE_DIR = Path(__file__).resolve().parent


def get_db_path() -> Path:
    configured = os.getenv("NOTE2QUIZ_DB_PATH")
    if configured:
        path = Path(configured)
        return path if path.is_absolute() else BASE_DIR.parent / path
    return BASE_DIR / "note2quiz.db"


def get_connection() -> sqlite3.Connection:
    db_path = get_db_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS uploaded_files (
                id TEXT PRIMARY KEY,
                original_filename TEXT NOT NULL,
                stored_path TEXT NOT NULL,
                extracted_text TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS study_packs (
                id TEXT PRIMARY KEY,
                file_id TEXT NOT NULL,
                title TEXT NOT NULL,
                summary TEXT NOT NULL,
                quiz_json TEXT NOT NULL,
                flashcards_json TEXT NOT NULL,
                key_terms_json TEXT NOT NULL,
                original_text TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(file_id) REFERENCES uploaded_files(id)
            )
            """
        )


def row_to_pack(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "id": row["id"],
        "file_id": row["file_id"],
        "title": row["title"],
        "summary": row["summary"],
        "quiz": json.loads(row["quiz_json"]),
        "flashcards": json.loads(row["flashcards_json"]),
        "key_terms": json.loads(row["key_terms_json"]),
        "original_text": row["original_text"],
        "created_at": row["created_at"],
    }
