from typing import Any


def safe_markdown_filename(title: str) -> str:
    cleaned = "".join(character if character.isalnum() or character in ("-", "_") else "_" for character in title)
    return f"{cleaned.strip('_') or 'study_pack'}.md"


def pack_to_markdown(pack: dict[str, Any]) -> str:
    lines = [
        f"# {pack['title']}",
        "",
        "## Summary",
        "",
        pack["summary"],
        "",
        "## Quiz",
        "",
    ]

    for index, item in enumerate(pack["quiz"], start=1):
        lines.append(f"{index}. {item.get('question', '')}")
        for choice in item.get("choices", []):
            lines.append(f"   - {choice}")
        lines.append(f"   - Answer: {item.get('answer', '')}")
        if item.get("explanation"):
            lines.append(f"   - Explanation: {item.get('explanation', '')}")
        lines.append("")

    lines.extend(["## Flashcards", ""])
    for index, item in enumerate(pack["flashcards"], start=1):
        lines.append(f"{index}. **{item.get('front', '')}**")
        lines.append(f"   {item.get('back', '')}")
        lines.append("")

    lines.extend(["## Key Terms", ""])
    for item in pack["key_terms"]:
        lines.append(f"- **{item.get('term', '')}**: {item.get('definition', '')}")

    lines.extend(["", "## Original Text", "", pack["original_text"]])
    if pack.get("translation_text"):
        translation_language = pack.get("translation_language") or "selected language"
        lines.extend(["", f"## Translation ({translation_language.title()})", "", pack["translation_text"]])
    return "\n".join(lines)
