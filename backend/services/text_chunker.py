from __future__ import annotations


def chunk_text(text: str, max_chars: int = 6000, overlap: int = 400) -> list[str]:
    compact = "\n".join(line.strip() for line in text.splitlines() if line.strip())
    if len(compact) <= max_chars:
        return [compact] if compact else []

    chunks: list[str] = []
    start = 0
    while start < len(compact):
        end = min(start + max_chars, len(compact))
        if end < len(compact):
            paragraph_break = compact.rfind("\n", start, end)
            sentence_break = max(compact.rfind(". ", start, end), compact.rfind("? ", start, end), compact.rfind("! ", start, end))
            best_break = max(paragraph_break, sentence_break)
            if best_break > start + max_chars // 2:
                end = best_break + 1
        chunks.append(compact[start:end].strip())
        if end >= len(compact):
            break
        start = max(end - overlap, start + 1)
    return [chunk for chunk in chunks if chunk]


def prepare_generation_text(text: str, max_chars: int = 22000) -> str:
    chunks = chunk_text(text)
    if len(chunks) == 1:
        return chunks[0][:max_chars]

    prepared: list[str] = []
    budget_per_chunk = max(1200, max_chars // max(len(chunks), 1))
    for index, chunk in enumerate(chunks, start=1):
        prepared.append(f"[Chunk {index}/{len(chunks)}]\n{chunk[:budget_per_chunk]}")
    return "\n\n".join(prepared)[:max_chars]
