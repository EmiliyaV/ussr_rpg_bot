from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from app.content.history import (
    get_context_word_counts,
    get_full_context_word_counts,
    get_total_turns,
)
from app.game.rules import MIN_YEAR_CONTEXT_WORDS


def main() -> None:
    unique_counts = get_context_word_counts()
    full_counts = get_full_context_word_counts()

    print(f"Total turns: {get_total_turns()}")
    print("Checking UNIQUE historical_focus word counts, not shared LLM context.")

    for year, words in unique_counts.items():
        full_words = full_counts.get(year, words)
        status = "OK" if words >= MIN_YEAR_CONTEXT_WORDS else "TOO SHORT"
        print(f"{year}: unique={words} words, full_context={full_words} words [{status}]")

    bad = {
        year: words
        for year, words in unique_counts.items()
        if words < MIN_YEAR_CONTEXT_WORDS
    }

    if bad:
        raise SystemExit(f"Some unique historical focuses are too short: {bad}")

    if get_total_turns() < 20:
        raise SystemExit(f"Expected 20 turns, got {get_total_turns()}")

    print("All unique historical focuses are valid.")


if __name__ == "__main__":
    main()
