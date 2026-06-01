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
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db() -> None:
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version INTEGER PRIMARY KEY,
                applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
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
                translation_text TEXT NOT NULL DEFAULT '',
                language TEXT NOT NULL DEFAULT 'english',
                translation_language TEXT NOT NULL DEFAULT 'none',
                key_terms_count INTEGER NOT NULL DEFAULT 10,
                quiz_order TEXT NOT NULL DEFAULT 'ranked',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(file_id) REFERENCES uploaded_files(id)
            )
            """
        )
        _apply_migration(
            conn,
            1,
            """
            CREATE INDEX IF NOT EXISTS idx_uploaded_files_created_at
            ON uploaded_files(created_at)
            """,
        )
        _apply_migration(
            conn,
            2,
            """
            CREATE INDEX IF NOT EXISTS idx_study_packs_created_at
            ON study_packs(created_at)
            """,
        )
        _apply_migration(
            conn,
            3,
            """
            CREATE UNIQUE INDEX IF NOT EXISTS idx_study_packs_file_id_unique
            ON study_packs(file_id)
            """,
        )
        _add_column_if_missing(conn, "study_packs", "translation_text", "TEXT NOT NULL DEFAULT ''")
        _add_column_if_missing(conn, "study_packs", "language", "TEXT NOT NULL DEFAULT 'english'")
        _add_column_if_missing(conn, "study_packs", "translation_language", "TEXT NOT NULL DEFAULT 'none'")
        _add_column_if_missing(conn, "study_packs", "key_terms_count", "INTEGER NOT NULL DEFAULT 10")
        _add_column_if_missing(conn, "study_packs", "quiz_order", "TEXT NOT NULL DEFAULT 'ranked'")
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS exam_attempts (
                id TEXT PRIMARY KEY,
                pack_id TEXT NOT NULL,
                score INTEGER NOT NULL DEFAULT 0,
                total_questions INTEGER NOT NULL DEFAULT 0,
                duration_seconds INTEGER,
                answers_json TEXT NOT NULL DEFAULT '[]',
                review_json TEXT NOT NULL DEFAULT '[]',
                status TEXT NOT NULL DEFAULT 'in_progress',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                completed_at TEXT,
                FOREIGN KEY(pack_id) REFERENCES study_packs(id) ON DELETE CASCADE
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS wrong_answers (
                id TEXT PRIMARY KEY,
                attempt_id TEXT NOT NULL,
                pack_id TEXT NOT NULL,
                question TEXT NOT NULL,
                user_answer TEXT NOT NULL,
                correct_answer TEXT NOT NULL,
                explanation TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(attempt_id) REFERENCES exam_attempts(id) ON DELETE CASCADE,
                FOREIGN KEY(pack_id) REFERENCES study_packs(id) ON DELETE CASCADE
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS study_plans (
                id TEXT PRIMARY KEY,
                pack_id TEXT NOT NULL,
                duration_days INTEGER NOT NULL,
                plan_json TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(pack_id) REFERENCES study_packs(id) ON DELETE CASCADE,
                UNIQUE(pack_id, duration_days)
            )
            """
        )


def _apply_migration(conn: sqlite3.Connection, version: int, sql: str) -> None:
    exists = conn.execute(
        "SELECT 1 FROM schema_migrations WHERE version = ?",
        (version,),
    ).fetchone()
    if exists:
        return
    conn.execute(sql)
    conn.execute("INSERT INTO schema_migrations (version) VALUES (?)", (version,))


def _add_column_if_missing(conn: sqlite3.Connection, table: str, column: str, definition: str) -> None:
    columns = {row["name"] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()}
    if column not in columns:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")


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
        "translation_text": row["translation_text"],
        "language": row["language"],
        "translation_language": row["translation_language"],
        "key_terms_count": row["key_terms_count"],
        "quiz_order": row["quiz_order"],
        "created_at": row["created_at"],
    }
