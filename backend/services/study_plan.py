from typing import Any


def mock_study_plan(pack: dict[str, Any], duration_days: int) -> list[dict[str, Any]]:
    key_terms = pack.get("key_terms", [])[: max(duration_days, 3)]
    flashcards = pack.get("flashcards", [])
    quiz = pack.get("quiz", [])
    summary = str(pack.get("summary") or "")
    days: list[dict[str, Any]] = []
    total_cards = len(flashcards)
    total_quiz = len(quiz)
    base_card_count = min(10, max(4, total_cards // max(duration_days, 1))) if total_cards else 0
    base_quiz_count = min(8, max(3, total_quiz // max(duration_days, 1))) if total_quiz else 0

    if duration_days == 1:
        return [
            {
                "day": 1,
                "focus": "Exam cram and active recall",
                "tasks": [
                    "Read the short summary once, then close it and write the main argument from memory.",
                    f"Review the top {min(len(key_terms), 8)} key terms in importance order and mark the weakest three.",
                    f"Run one timed quiz set with all {total_quiz or 'available'} questions.",
                    "Review every wrong answer immediately and rewrite the explanation in your own words.",
                    f"Practice {min(total_cards, 20) or 'all'} flashcards, then repeat only cards marked Need review.",
                    "Finish with a 10-minute final scan of definitions, formulas, dates, or examples.",
                ],
                "goal": "Leave with a compact exam sheet: hardest terms, missed questions, and final must-remember points.",
            }
        ]

    for index in range(duration_days):
        term = key_terms[index % len(key_terms)] if key_terms else {"term": "Core ideas"}
        focus = term.get("term", "Core ideas")
        is_first = index == 0
        is_last = index == duration_days - 1
        midpoint = index >= max(1, duration_days // 2)

        if is_first:
            tasks = [
                "Skim the original text and turn the summary into a 5-bullet personal outline.",
                f"Learn the first {min(len(key_terms), max(3, duration_days))} high-importance key terms.",
                f"Practice {base_card_count or 'a small set of'} flashcards and mark Need review honestly.",
                "Answer a short diagnostic quiz without notes to expose weak areas.",
                "Write down two questions you still cannot explain clearly.",
            ]
            goal = "Build the map: know what the pack covers and where your weak areas are."
        elif is_last:
            tasks = [
                "Review only the marked weak topics and any saved favorites.",
                f"Take a final mixed quiz using {total_quiz or 'all available'} questions.",
                "Redo every wrong answer and explain why the correct answer wins.",
                "Practice only Need review flashcards until the stack is empty or time runs out.",
                "Create a final one-page cram sheet from the summary, key terms, and explanations.",
            ]
            goal = "Convert review into exam readiness: fast recall, fewer repeated mistakes, clear explanations."
        elif midpoint:
            tasks = [
                f"Deep-review {focus} using the source text and the detailed summary.",
                f"Practice {base_card_count} flashcards, prioritizing cards previously marked Need review.",
                f"Answer {base_quiz_count} quiz questions in random order.",
                "Group wrong answers by topic and write one correction rule for each group.",
                "Teach the concept aloud in under two minutes without looking at the notes.",
            ]
            goal = f"Move from recognition to recall for {focus} and related weak topics."
        else:
            tasks = [
                f"Study {focus} and connect it to at least two other key terms.",
                f"Practice {base_card_count} new flashcards and favorite the most useful ones.",
                f"Answer {base_quiz_count} ranked quiz questions from foundational to harder ideas.",
                "Compare your answers with explanations and mark any repeated confusion.",
                "Write a short example or application from the original lecture material.",
            ]
            goal = f"Strengthen understanding of {focus} before moving into mixed practice."

        days.append(
            {
                "day": index + 1,
                "focus": focus,
                "tasks": tasks,
                "goal": goal,
            }
        )

    if summary:
        days[0]["tasks"].insert(0, "Start by reading the generated summary and highlighting anything that feels unfamiliar.")
    return days
