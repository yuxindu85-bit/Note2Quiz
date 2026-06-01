import json
import os
from typing import Any

import httpx


MAX_PROMPT_CHARS = 24000


async def generate_study_pack(text: str, title: str) -> dict[str, Any]:
    api_key = os.getenv("AI_API_KEY")
    if not api_key:
        return mock_study_pack(title, text)

    base_url = os.getenv("AI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
    model = os.getenv("AI_MODEL", "gpt-4o-mini")
    prompt = _build_prompt(title, text[:MAX_PROMPT_CHARS])

    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.post(
            f"{base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": model,
                "messages": [
                    {
                        "role": "system",
                        "content": "You create structured study material. Return only valid JSON.",
                    },
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.3,
                "response_format": {"type": "json_object"},
            },
        )
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]

    return normalize_pack(json.loads(content), title, text)


def _build_prompt(title: str, text: str) -> str:
    return f"""
Create a study pack for this lecture file: {title}

Return JSON with exactly these keys:
- title: string
- summary: concise but useful study summary
- quiz: array of 10 objects with question, choices array of 4 strings, answer string
- flashcards: array of 20 objects with front and back
- key_terms: array of objects with term and definition

Lecture text:
{text}
""".strip()


def normalize_pack(data: dict[str, Any], fallback_title: str, original_text: str) -> dict[str, Any]:
    fallback = mock_study_pack(fallback_title, original_text)
    return {
        "title": str(data.get("title") or fallback_title),
        "summary": str(data.get("summary") or "No summary was generated."),
        "quiz": _with_fallback(_list_of_dicts(data.get("quiz"), 10), fallback["quiz"], 10),
        "flashcards": _with_fallback(_list_of_dicts(data.get("flashcards"), 20), fallback["flashcards"], 20),
        "key_terms": _with_fallback(_list_of_dicts(data.get("key_terms"), 12), fallback["key_terms"], 8),
        "original_text": original_text,
    }


def _list_of_dicts(value: Any, expected: int) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    cleaned = [item for item in value if isinstance(item, dict)]
    return cleaned[:expected]


def _with_fallback(items: list[dict[str, Any]], fallback: list[dict[str, Any]], expected: int) -> list[dict[str, Any]]:
    merged = items + fallback
    return merged[:expected]


def mock_study_pack(title: str, text: str) -> dict[str, Any]:
    words = [word.strip(".,:;()[]").lower() for word in text.split()]
    candidates = []
    for word in words:
        if len(word) > 5 and word.isalpha() and word not in candidates:
            candidates.append(word)
        if len(candidates) >= 10:
            break

    theme = candidates[0].title() if candidates else "Lecture"
    quiz = [
        {
            "question": f"Mock question {index}: Which idea is emphasized in {title}?",
            "choices": [theme, "Unrelated detail", "Formatting only", "Page numbering"],
            "answer": theme,
        }
        for index in range(1, 11)
    ]
    flashcards = [
        {
            "front": f"{theme} concept {index}",
            "back": "Review the uploaded lecture text and connect this concept to the summary.",
        }
        for index in range(1, 21)
    ]
    key_terms = [
        {
            "term": candidate.title(),
            "definition": f"A recurring term detected in the uploaded notes for {title}.",
        }
        for candidate in (candidates[:8] or ["lecture", "summary", "review"])
    ]

    return {
        "title": title,
        "summary": (
            "Mock summary: this study pack was generated without an AI API key. "
            "The uploaded text was parsed successfully and can be reviewed in the Original Text tab."
        ),
        "quiz": quiz,
        "flashcards": flashcards,
        "key_terms": key_terms,
        "original_text": text,
    }
