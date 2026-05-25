import re

from app.domain.models import HistoryTurn
from app.game.rules import MIN_YEAR_CONTEXT_WORDS, PREVIOUS_CONTEXT_WORDS


WORD_RE = re.compile(r"[A-Za-zА-Яа-яЁё0-9]+(?:-[A-Za-zА-Яа-яЁё0-9]+)?")


def count_words(text: str) -> int:
    return len(WORD_RE.findall(text))


def trim_to_word_limit(text: str, max_words: int) -> str:
    words = WORD_RE.findall(text)

    if len(words) <= max_words:
        return text.strip()

    return " ".join(words[:max_words]).strip() + "..."


def build_year_context_for_llm(
    history_turn: HistoryTurn,
    min_words: int = MIN_YEAR_CONTEXT_WORDS,
) -> str:
    word_count = count_words(history_turn.context)

    if word_count < min_words:
        raise RuntimeError(
            f"LLM context for {history_turn.year} is too short: "
            f"{word_count} words, expected at least {min_words}."
        )

    return history_turn.context.strip()


def build_previous_answers_context(
    memory: list[str],
    max_words: int = PREVIOUS_CONTEXT_WORDS,
) -> str:
    if not memory:
        return "Предыдущих решений пока нет."

    raw_context = "\n".join(f"- {item}" for item in memory[-8:])
    return trim_to_word_limit(raw_context, max_words)
