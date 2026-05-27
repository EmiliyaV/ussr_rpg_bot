from pathlib import Path
import inspect
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from app.content.history import HISTORY_TURNS, get_context_word_counts
from app.game.rules import MIN_YEAR_CONTEXT_WORDS
from app.ui.keyboards import choices_keyboard
from app.ui import messages


def check(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit("[FAIL] " + message)
    print("[OK] " + message)


def main() -> None:
    first_turn = HISTORY_TURNS[0]
    keyboard = choices_keyboard(first_turn)
    choice_callbacks = [
        button.callback_data
        for row in keyboard.inline_keyboard
        for button in row
        if button.callback_data and button.callback_data.startswith("choice:")
    ]

    check(
        all(callback.startswith(f"choice:{first_turn.turn}:") for callback in choice_callbacks),
        "callback выбора привязан к номеру хода",
    )

    debug_source = inspect.getsource(messages.help_message)
    check(
        "DEBUG_COMMANDS_ENABLED=true" in debug_source,
        "help уточняет, что debug_status включается env-флагом",
    )

    counts = get_context_word_counts()
    check(
        all(words >= MIN_YEAR_CONTEXT_WORDS for words in counts.values()),
        "600 слов проверяются по уникальному historical_focus",
    )

    for turn in HISTORY_TURNS:
        check(bool(turn.real_facts), f"{turn.year}: real_facts заполнены")
        check(bool(turn.player_limits), f"{turn.year}: player_limits заполнены")

    print("Final polish checks passed.")


if __name__ == "__main__":
    main()
