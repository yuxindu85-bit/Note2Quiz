import json
import os
import re
from collections import Counter
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

    return normalize_pack(_parse_json_object(content), title, text)


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


def _parse_json_object(content: str) -> dict[str, Any]:
    try:
        parsed = json.loads(content)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", content, flags=re.DOTALL)
        if not match:
            raise
        parsed = json.loads(match.group(0))

    if not isinstance(parsed, dict):
        raise ValueError("AI response must be a JSON object.")
    return parsed


def _list_of_dicts(value: Any, expected: int) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    cleaned = [item for item in value if isinstance(item, dict)]
    return cleaned[:expected]


def _with_fallback(
    items: list[dict[str, Any]],
    fallback: list[dict[str, Any]],
    expected: int,
) -> list[dict[str, Any]]:
    merged = items + fallback
    return merged[:expected]


def mock_study_pack(title: str, text: str) -> dict[str, Any]:
    sentences = _extract_sentences(text)
    keywords = _extract_keywords(text)
    primary_terms = keywords[:12] or ["lecture", "concept", "review", "example"]
    summary_topic = ", ".join(term.title() for term in primary_terms[:4]) or "core course concepts"

    quiz = _mock_quiz(title, sentences, primary_terms)
    flashcards = _mock_flashcards(sentences, primary_terms)
    key_terms = [
        {
            "term": candidate.title(),
            "definition": _definition_for_term(candidate, sentences, title),
        }
        for candidate in primary_terms[:10]
    ]

    return {
        "title": title,
        "summary": (
            f"Demo summary: this pack highlights {summary_topic}. The upload was parsed successfully, "
            "and Note2Quiz generated practice material locally because AI_API_KEY is not set."
        ),
        "quiz": quiz,
        "flashcards": flashcards,
        "key_terms": key_terms,
        "original_text": text,
    }


def _extract_sentences(text: str) -> list[str]:
    chunks = re.split(r"(?<=[.!?])\s+|\n+", text)
    sentences = [chunk.strip(" -\t\r\n") for chunk in chunks if len(chunk.strip()) >= 24]
    if sentences:
        return sentences[:12]
    compact = " ".join(text.split())
    return [compact[:220]] if compact else ["Review the uploaded material and identify the main ideas."]


def _extract_keywords(text: str) -> list[str]:
    stopwords = {
        "about",
        "after",
        "also",
        "because",
        "between",
        "could",
        "during",
        "every",
        "first",
        "from",
        "have",
        "into",
        "more",
        "other",
        "should",
        "study",
        "their",
        "there",
        "these",
        "this",
        "through",
        "while",
        "with",
        "would",
    }
    words = re.findall(r"[A-Za-z][A-Za-z-]{4,}", text.lower())
    counts = Counter(word for word in words if word not in stopwords)
    return [word for word, _count in counts.most_common(24)]


def _mock_quiz(title: str, sentences: list[str], keywords: list[str]) -> list[dict[str, Any]]:
    templates = [
        "Which concept is most central to this note?",
        "Which term should a student define first?",
        "What topic is most likely to appear on a review quiz?",
        "Which idea best matches the uploaded lecture?",
        "Which item belongs in the key terms list?",
        "What should be connected to the summary?",
        "Which phrase is directly supported by the source text?",
        "Which concept deserves a flashcard?",
        "What is a useful exam focus from this material?",
        f"What is the strongest study signal in {title}?",
    ]
    distractors = [
        "page margins",
        "slide transitions",
        "file naming",
        "citation style",
        "attendance policy",
        "font selection",
        "printing settings",
        "desktop shortcuts",
        "folder sorting",
        "keyboard layout",
    ]
    quiz: list[dict[str, Any]] = []
    for index in range(10):
        answer = keywords[index % len(keywords)].title()
        sentence = sentences[index % len(sentences)]
        choices = [answer]
        while len(choices) < 4:
            distractor = distractors[(index + len(choices) - 1) % len(distractors)]
            choices.append(distractor.title())
        quiz.append(
            {
                "question": f"{templates[index]} Context: {sentence[:110]}",
                "choices": choices[:4],
                "answer": answer,
            }
        )
    return quiz


def _mock_flashcards(sentences: list[str], keywords: list[str]) -> list[dict[str, str]]:
    cards: list[dict[str, str]] = []
    for index in range(20):
        term = keywords[index % len(keywords)].title()
        sentence = sentences[index % len(sentences)]
        cards.append(
            {
                "front": f"{term}: what should you remember?",
                "back": f"{sentence[:180]}",
            }
        )
    return cards


def _definition_for_term(term: str, sentences: list[str], title: str) -> str:
    matching_sentence = next((sentence for sentence in sentences if term.lower() in sentence.lower()), "")
    if matching_sentence:
        return matching_sentence[:180]
    return f"A recurring concept detected in {title}; review the source text for its role in the lecture."
