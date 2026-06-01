from typing import Any


def mock_study_plan(pack: dict[str, Any], duration_days: int) -> list[dict[str, Any]]:
    key_terms = pack.get("key_terms", [])[: max(duration_days, 3)]
    flashcards = pack.get("flashcards", [])
    quiz = pack.get("quiz", [])
    days: list[dict[str, Any]] = []

    for index in range(duration_days):
        term = key_terms[index % len(key_terms)] if key_terms else {"term": "Core ideas"}
        card_count = min(8, max(3, len(flashcards) // max(duration_days, 1)))
        quiz_count = min(5, max(2, len(quiz) // max(duration_days, 1)))
        days.append(
            {
                "day": index + 1,
                "focus": term.get("term", "Core ideas"),
                "tasks": [
                    "Review the summary and mark anything unclear.",
                    f"Study {card_count} flashcards connected to this focus area.",
                    f"Answer {quiz_count} quiz questions without notes.",
                    "Write a one-paragraph explanation from memory.",
                ],
                "goal": f"Be able to explain {term.get('term', 'the main concept')} using the source notes.",
            }
        )

    return days
