from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from app.content.history import get_context_word_counts, get_total_turns
from app.game.rules import MIN_YEAR_CONTEXT_WORDS

counts = get_context_word_counts()
print(f"Total turns: {get_total_turns()}")

for year, words in counts.items():
    status = "OK" if words >= MIN_YEAR_CONTEXT_WORDS else "TOO SHORT"
    print(f"{year}: {words} words [{status}]")

bad = {year: words for year, words in counts.items() if words < MIN_YEAR_CONTEXT_WORDS}
if bad:
    raise SystemExit(f"Some contexts are too short: {bad}")

if get_total_turns() < 20:
    raise SystemExit(f"Expected 20 turns, got {get_total_turns()}")

print("All contexts are valid.")
