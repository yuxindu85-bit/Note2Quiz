import json
import os
import random
import re
from collections import Counter
from typing import Any

import httpx

from services.text_chunker import prepare_generation_text


MAX_PROMPT_CHARS = 24000
LANGUAGE_LABELS = {
    "auto": "Auto-detected source language",
    "english": "English",
    "chinese": "Chinese",
    "french": "French",
    "russian": "Russian",
    "spanish": "Spanish",
}


async def generate_study_pack(
    text: str,
    title: str,
    quiz_count: int = 10,
    key_terms_count: int = 10,
    quiz_order: str = "ranked",
    language: str = "english",
    translation_language: str = "none",
) -> dict[str, Any]:
    quiz_count = max(3, min(quiz_count, 30))
    key_terms_count = max(3, min(key_terms_count, 30))
    quiz_order = quiz_order if quiz_order in {"ranked", "random"} else "ranked"
    requested_language = language if language in LANGUAGE_LABELS else "auto"
    language = _detect_language(text) if requested_language == "auto" else requested_language
    translation_language = translation_language if translation_language in LANGUAGE_LABELS else "none"
    include_translation = translation_language != "none"
    api_key = os.getenv("AI_API_KEY")
    if not api_key:
        return mock_study_pack(
            title,
            text,
            quiz_count,
            key_terms_count,
            quiz_order,
            language,
            translation_language=translation_language,
            include_translation=include_translation,
        )

    base_url = os.getenv("AI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
    model = os.getenv("AI_MODEL", "gpt-4o-mini")
    generation_text = prepare_generation_text(text, max_chars=MAX_PROMPT_CHARS)
    prompt = _build_prompt(
        title,
        generation_text,
        key_terms_count,
        quiz_count,
        quiz_order,
        language,
        translation_language=translation_language,
        include_translation=include_translation,
    )

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

    return normalize_pack(
        _parse_json_object(content),
        title,
        text,
        key_terms_count,
        quiz_count,
        quiz_order,
        language,
        translation_language=translation_language,
        include_translation=include_translation,
    )


def _build_prompt(
    title: str,
    text: str,
    key_terms_count: int,
    quiz_count: int,
    quiz_order: str,
    language: str,
    translation_language: str,
    include_translation: bool,
) -> str:
    language_label = LANGUAGE_LABELS[language]
    translation_label = LANGUAGE_LABELS.get(translation_language, "")
    order_instruction = (
        "Order quiz questions from most foundational to more advanced."
        if quiz_order == "ranked"
        else "Randomize the quiz question order while keeping answers correct."
    )
    return f"""
Create a study pack for this lecture file: {title}

Return JSON with exactly these keys:
- title: string
- summary: object with short, detailed, and bullet_points array in {language_label}
- quiz: array of exactly {quiz_count} objects with question, choices array of 4 strings, answer string, explanation string
- quiz items must also include topic and difficulty ("easy", "medium", or "hard")
- flashcards: array of 20 objects with front, back, and topic
- key_terms: array of exactly {key_terms_count} objects with term, short definition, and importance ("high", "medium", or "low"), ordered by importance
- translation_text: {"translated version of the lecture text in " + translation_label if include_translation else "empty string"}

Rules:
- Write all generated study content in the same language as the lecture text, currently detected as {language_label}.
- {order_instruction}
- Do not invent unsupported facts. Use the lecture text as the source.

Lecture text:
{text}
""".strip()


def normalize_pack(
    data: dict[str, Any],
    fallback_title: str,
    original_text: str,
    key_terms_count: int,
    quiz_count: int,
    quiz_order: str,
    language: str,
    translation_language: str,
    include_translation: bool,
) -> dict[str, Any]:
    fallback = mock_study_pack(
        fallback_title,
        original_text,
        quiz_count,
        key_terms_count,
        quiz_order,
        language,
        translation_language=translation_language,
        include_translation=include_translation,
    )
    return {
        "title": str(data.get("title") or fallback_title),
        "summary": _summary_to_text(data.get("summary"), fallback["summary"]),
        "quiz": _normalize_quiz(_with_fallback(_list_of_dicts(data.get("quiz"), quiz_count), fallback["quiz"], quiz_count)),
        "flashcards": _normalize_flashcards(_with_fallback(_list_of_dicts(data.get("flashcards"), 20), fallback["flashcards"], 20)),
        "key_terms": _normalize_key_terms(_with_fallback(_list_of_dicts(data.get("key_terms"), key_terms_count), fallback["key_terms"], key_terms_count)),
        "original_text": original_text,
        "translation_text": str(data.get("translation_text") or fallback["translation_text"]) if include_translation else "",
        "language": language,
        "translation_language": translation_language,
        "quiz_count": quiz_count,
        "key_terms_count": key_terms_count,
        "quiz_order": quiz_order,
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


def _summary_to_text(value: Any, fallback: str) -> str:
    if isinstance(value, dict):
        short = str(value.get("short") or "").strip()
        detailed = str(value.get("detailed") or "").strip()
        bullets = value.get("bullet_points")
        bullet_text = ""
        if isinstance(bullets, list):
            bullet_text = "\n".join(f"- {item}" for item in bullets if item)
        return "\n\n".join(part for part in [short, detailed, bullet_text] if part) or fallback
    if value:
        return str(value)
    return fallback


def _normalize_quiz(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for item in items:
        choices = item.get("choices") if isinstance(item.get("choices"), list) else []
        answer = str(item.get("answer") or (choices[0] if choices else ""))
        normalized.append(
            {
                "question": str(item.get("question") or "Review this source-backed idea."),
                "choices": [str(choice) for choice in choices[:4]],
                "answer": answer,
                "explanation": str(item.get("explanation") or f"The correct answer is supported by the study material: {answer}"),
                "topic": str(item.get("topic") or "General"),
                "difficulty": str(item.get("difficulty") or "medium"),
            }
        )
    return normalized


def _normalize_flashcards(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "front": str(item.get("front") or ""),
            "back": str(item.get("back") or ""),
            "topic": str(item.get("topic") or "General"),
        }
        for item in items
    ]


def _normalize_key_terms(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "term": str(item.get("term") or ""),
            "definition": str(item.get("definition") or ""),
            "importance": str(item.get("importance") or "medium"),
        }
        for item in items
    ]


def mock_study_pack(
    title: str,
    text: str,
    quiz_count: int = 10,
    key_terms_count: int = 10,
    quiz_order: str = "ranked",
    language: str = "english",
    translation_language: str = "none",
    include_translation: bool = False,
) -> dict[str, Any]:
    sentences = _extract_sentences(text)
    keywords = _extract_keywords(text)
    primary_terms = keywords[: max(key_terms_count, 12)] or ["lecture", "concept", "review", "example"]
    summary_topic = ", ".join(term.title() for term in primary_terms[:4]) or "core course concepts"

    quiz = _mock_quiz(title, sentences, primary_terms, quiz_count, quiz_order)
    flashcards = _mock_flashcards(sentences, primary_terms)
    key_terms = [
        {
            "term": candidate.title(),
            "definition": _definition_for_term(candidate, sentences, title),
            "importance": "high" if index < 5 else "medium",
        }
        for index, candidate in enumerate(primary_terms[:key_terms_count])
    ]
    language_label = LANGUAGE_LABELS.get(language, "English")

    return {
        "title": title,
        "summary": (
            f"Demo summary ({language_label} mode): this pack highlights {summary_topic}. "
            f"Key terms are ordered by importance and limited to {key_terms_count}. "
            "Note2Quiz generated this locally because AI_API_KEY is not set."
        ),
        "quiz": quiz,
        "flashcards": flashcards,
        "key_terms": key_terms,
        "original_text": text,
        "translation_text": _mock_translation(text, translation_language) if include_translation else "",
        "language": language,
        "translation_language": translation_language,
        "quiz_count": quiz_count,
        "key_terms_count": key_terms_count,
        "quiz_order": quiz_order,
    }


def _extract_sentences(text: str) -> list[str]:
    compact = " ".join(text.split())
    chunks = re.split(r"(?<=[.!?])\s+", compact)
    sentences = [chunk.strip(" -\t\r\n") for chunk in chunks if len(chunk.strip()) >= 24]
    if sentences:
        return sentences[:18]
    return [compact[:220]] if compact else ["Review the uploaded material and identify the main ideas."]


def _detect_language(text: str) -> str:
    sample = text[:6000].lower()
    if re.search(r"[\u4e00-\u9fff]", sample):
        return "chinese"
    if re.search(r"[\u0400-\u04ff]", sample):
        return "russian"
    french_markers = [" le ", " la ", " les ", " des ", " une ", " est ", " avec ", " pour ", " dans ", "é", "è", "à", "ç"]
    spanish_markers = [" el ", " la ", " los ", " las ", " una ", " que ", " con ", " para ", "ción", "ñ", "¿", "¡"]
    french_score = sum(sample.count(marker) for marker in french_markers)
    spanish_score = sum(sample.count(marker) for marker in spanish_markers)
    if french_score >= 3 and french_score > spanish_score:
        return "french"
    if spanish_score >= 3 and spanish_score > french_score:
        return "spanish"
    return "english"


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


def _mock_quiz(
    title: str,
    sentences: list[str],
    keywords: list[str],
    quiz_count: int = 10,
    quiz_order: str = "ranked",
) -> list[dict[str, Any]]:
    question_stems = [
        "Which statement best explains {term}?",
        "What should you remember about {term}?",
        "Which source-backed fact is most connected to {term}?",
        "Which answer would be strongest on a quiz about {term}?",
        "Which statement is supported by the uploaded notes about {term}?",
        "Which explanation best fits {term}?",
        "What is the clearest study takeaway for {term}?",
        "Which detail belongs in a summary of {term}?",
        "Which option accurately reflects the notes on {term}?",
        "In {title}, what is the best answer about {term}?",
    ]
    fact_pool = _fact_pool(sentences)
    quiz: list[dict[str, Any]] = []
    for index in range(quiz_count):
        term = keywords[index % len(keywords)].title()
        answer = fact_pool[index % len(fact_pool)]
        choices = [answer]
        offset = 1
        while len(choices) < 4:
            distractor = fact_pool[(index + offset) % len(fact_pool)]
            if distractor not in choices:
                choices.append(distractor)
            offset += 1
            if offset > len(fact_pool) + 4:
                choices.append(_generic_distractor(len(choices)))
        quiz.append(
            {
                "question": question_stems[index % len(question_stems)].format(term=term, title=title),
                "choices": choices[:4],
                "answer": answer,
                "explanation": f"This answer is correct because the uploaded notes explicitly support this point: {answer}",
                "topic": term,
                "difficulty": "easy" if index < max(1, quiz_count // 3) else "medium" if index < max(2, quiz_count * 2 // 3) else "hard",
            }
        )
    if quiz_order == "random":
        seeded = random.Random(f"{title}:{len(' '.join(sentences))}:{','.join(keywords[:6])}")
        seeded.shuffle(quiz)
    return quiz


def _mock_flashcards(sentences: list[str], keywords: list[str]) -> list[dict[str, str]]:
    prompts = [
        "Define {term}.",
        "Why does {term} matter?",
        "What is the key fact about {term}?",
        "How would you explain {term} in one sentence?",
        "What should you connect {term} to?",
    ]
    cards: list[dict[str, str]] = []
    for index in range(20):
        term = keywords[index % len(keywords)].title()
        sentence = sentences[index % len(sentences)]
        prompt = prompts[index % len(prompts)].format(term=term)
        cards.append(
            {
                "front": prompt,
                "back": _flashcard_answer(term, sentence),
                "topic": term,
            }
        )
    return cards


def _definition_for_term(term: str, sentences: list[str], title: str) -> str:
    matching_sentence = next((sentence for sentence in sentences if term.lower() in sentence.lower()), "")
    if matching_sentence:
        return matching_sentence[:180]
    return f"A recurring concept detected in {title}; review the source text for its role in the lecture."


def _fact_pool(sentences: list[str]) -> list[str]:
    facts = [_clean_fact(sentence) for sentence in sentences if sentence.strip()]
    facts = [fact for fact in facts if len(fact) >= 20]
    while len(facts) < 4:
        facts.append(_generic_distractor(len(facts)))
    return facts[:12]


def _clean_fact(sentence: str) -> str:
    sentence = " ".join(sentence.split())
    if len(sentence) <= 150:
        return sentence
    return f"{sentence[:147].rstrip()}..."


def _generic_distractor(index: int) -> str:
    distractors = [
        "The notes focus mainly on formatting choices rather than course content.",
        "The material says the topic is unrelated to the uploaded lecture.",
        "The source text only describes file storage and does not include study ideas.",
        "The lecture states that this concept should be ignored during review.",
    ]
    return distractors[index % len(distractors)]


def _flashcard_answer(term: str, sentence: str) -> str:
    clean_sentence = _clean_fact(sentence)
    if term.lower() in clean_sentence.lower():
        return clean_sentence
    return f"Connect {term} to this source fact: {clean_sentence}"


def _mock_translation(text: str, language: str) -> str:
    clean = " ".join(text.split())
    if not clean:
        return ""
    if language == "english":
        return clean

    label = LANGUAGE_LABELS.get(language, language.title())
    return (
        f"Demo mode cannot produce a reliable full-article {label} translation without AI_API_KEY. "
        "The original text is shown above. Add an OpenAI-compatible API key to generate an accurate translation here."
    )


def _dictionary_translate(text: str, language: str) -> str:
    dictionaries = {
        "chinese": {
            "price": "价格",
            "prices": "价格",
            "pricing": "定价",
            "consumer": "消费者",
            "consumers": "消费者",
            "company": "公司",
            "companies": "公司",
            "market": "市场",
            "buyers": "买方",
            "sellers": "卖方",
            "data": "数据",
            "technology": "技术",
            "personalised": "个性化",
            "personalized": "个性化",
            "discounts": "折扣",
            "coupons": "优惠券",
            "airline": "航空公司",
            "tickets": "机票",
            "efficient": "有效率的",
            "theory": "理论",
            "lecture": "讲座",
        },
        "french": {
            "price": "prix",
            "prices": "prix",
            "pricing": "tarification",
            "consumer": "consommateur",
            "consumers": "consommateurs",
            "company": "entreprise",
            "companies": "entreprises",
            "market": "marche",
            "buyers": "acheteurs",
            "sellers": "vendeurs",
            "data": "donnees",
            "technology": "technologie",
            "personalised": "personnalise",
            "personalized": "personnalise",
            "discounts": "reductions",
            "coupons": "coupons",
            "airline": "compagnie aerienne",
            "tickets": "billets",
            "efficient": "efficace",
            "theory": "theorie",
            "lecture": "cours",
        },
        "russian": {
            "price": "цена",
            "prices": "цены",
            "pricing": "ценообразование",
            "consumer": "потребитель",
            "consumers": "потребители",
            "company": "компания",
            "companies": "компании",
            "market": "рынок",
            "buyers": "покупатели",
            "sellers": "продавцы",
            "data": "данные",
            "technology": "технология",
            "personalised": "персонализированный",
            "personalized": "персонализированный",
            "discounts": "скидки",
            "coupons": "купоны",
            "airline": "авиакомпания",
            "tickets": "билеты",
            "efficient": "эффективный",
            "theory": "теория",
            "lecture": "лекция",
        },
        "spanish": {
            "price": "precio",
            "prices": "precios",
            "pricing": "fijacion de precios",
            "consumer": "consumidor",
            "consumers": "consumidores",
            "company": "empresa",
            "companies": "empresas",
            "market": "mercado",
            "buyers": "compradores",
            "sellers": "vendedores",
            "data": "datos",
            "technology": "tecnologia",
            "personalised": "personalizado",
            "personalized": "personalizado",
            "discounts": "descuentos",
            "coupons": "cupones",
            "airline": "aerolinea",
            "tickets": "boletos",
            "efficient": "eficiente",
            "theory": "teoria",
            "lecture": "clase",
        },
    }
    replacements = dictionaries.get(language, {})

    def replace_word(match: re.Match[str]) -> str:
        word = match.group(0)
        replacement = replacements.get(word.lower())
        if replacement is None:
            return word
        return replacement.title() if word[:1].isupper() else replacement

    return re.sub(r"[A-Za-z][A-Za-z-]*", replace_word, text)
