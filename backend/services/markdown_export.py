from typing import Any


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
    return "\n".join(lines)
