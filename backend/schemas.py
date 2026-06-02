from typing import Any, Optional

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
    explanation: str = ""
    topic: str = "General"
    difficulty: str = "medium"


class Flashcard(BaseModel):
    front: str
    back: str
    topic: str = "General"


class KeyTerm(BaseModel):
    term: str
    definition: str
    importance: str = "medium"


class GenerateOptions(BaseModel):
    quiz_count: int = Field(default=10, ge=3, le=30)
    key_terms_count: int = Field(default=10, ge=3, le=30)
    quiz_order: str = Field(default="ranked", pattern="^(ranked|random)$")
    language: str = Field(default="auto", pattern="^(auto|english|chinese|french|russian|spanish)$")
    translation_language: str = Field(default="none", pattern="^(none|english|chinese|french|russian|spanish)$")
    force: bool = False


class StudyPack(BaseModel):
    id: str
    file_id: str
    title: str
    summary: str
    quiz: list[dict[str, Any]]
    flashcards: list[dict[str, Any]]
    key_terms: list[dict[str, Any]]
    original_text: str
    translation_text: str = ""
    language: str = "english"
    translation_language: str = "none"
    quiz_count: int = 10
    key_terms_count: int = 10
    quiz_order: str = "ranked"
    created_at: str


class StudyPackListItem(BaseModel):
    id: str
    file_id: str
    title: str
    summary: str
    created_at: str


class StudyPackListResponse(BaseModel):
    packs: list[StudyPackListItem]


class ExamStartResponse(BaseModel):
    attempt_id: str
    pack_id: str
    title: str
    questions: list[dict[str, Any]]


class ExamAnswer(BaseModel):
    question_index: int
    answer: str


class ExamSubmitRequest(BaseModel):
    attempt_id: Optional[str] = None
    answers: list[ExamAnswer]
    duration_seconds: Optional[int] = Field(default=None, ge=0)


class ExamSubmitResponse(BaseModel):
    attempt_id: str
    pack_id: str
    score: int
    total_questions: int
    percentage: float = 0
    review: list[dict[str, Any]]


class ExamAttemptListItem(BaseModel):
    id: str
    pack_id: str
    title: str
    score: int
    total_questions: int
    percentage: float = 0
    duration_seconds: Optional[int] = None
    status: str
    created_at: str
    completed_at: Optional[str] = None


class ExamAttemptListResponse(BaseModel):
    attempts: list[ExamAttemptListItem]


class WrongAnswerListItem(BaseModel):
    id: str
    attempt_id: str
    pack_id: str
    pack_title: str
    question: str
    user_answer: str
    correct_answer: str
    explanation: str
    weak_topic: str = "General"
    reviewed: bool = False
    review_count: int = 0
    created_at: str


class WrongAnswerListResponse(BaseModel):
    wrong_answers: list[WrongAnswerListItem]


class StudyPlanRequest(BaseModel):
    duration_days: int = Field(default=3, ge=1, le=7)


class StudyPlanResponse(BaseModel):
    id: str
    pack_id: str
    duration_days: int
    plan: list[dict[str, Any]]
    created_at: str


class FavoriteItem(BaseModel):
    id: str
    pack_id: str
    item_type: str
    item_index: int
    title: str
    content: str
    source: str = ""
    created_at: str


class FavoriteCreateRequest(BaseModel):
    item_type: str
    item_index: int = 0
    title: str
    content: str
    source: str = ""


class FavoriteListResponse(BaseModel):
    favorites: list[FavoriteItem]


class FlashcardReviewRequest(BaseModel):
    card_index: int = Field(ge=0)
    status: str = Field(pattern="^(known|review)$")
