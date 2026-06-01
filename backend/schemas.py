from typing import Any

from pydantic import BaseModel, Field


class UploadResponse(BaseModel):
    file_id: str
    filename: str
    text_length: int
    preview: str


class HealthResponse(BaseModel):
    status: str
    database: str
    demo_mode: bool
    ai_model: str


class QuizItem(BaseModel):
    question: str
    choices: list[str] = Field(default_factory=list)
    answer: str


class Flashcard(BaseModel):
    front: str
    back: str


class KeyTerm(BaseModel):
    term: str
    definition: str


class StudyPack(BaseModel):
    id: str
    file_id: str
    title: str
    summary: str
    quiz: list[dict[str, Any]]
    flashcards: list[dict[str, Any]]
    key_terms: list[dict[str, Any]]
    original_text: str
    created_at: str


class StudyPackListItem(BaseModel):
    id: str
    file_id: str
    title: str
    summary: str
    created_at: str


class StudyPackListResponse(BaseModel):
    packs: list[StudyPackListItem]
