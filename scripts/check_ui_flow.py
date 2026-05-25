from pathlib import Path
import inspect
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from app.ui import keyboards, messages
import app.main as main_module


def check(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit("[FAIL] " + message)

    print("[OK] " + message)


def main() -> None:
    keyboard_source = inspect.getsource(keyboards)
    message_source = inspect.getsource(messages)
    main_source = inspect.getsource(main_module)

    check("next_turn_keyboard" in keyboard_source, "есть клавиатура Далее")
    check('callback_data="next_turn"' in keyboard_source, "кнопка Далее имеет callback next_turn")
    check("choice.id" in keyboard_source, "кнопки выбора используют короткие A/B/C")
    check("choice.text" not in keyboard_source, "полный текст выбора не выводится на кнопках")

    check("_normalize_text" in message_source, "есть нормализация текста")
    check("_extract_short_context" in message_source, "есть извлечение короткого контекста")
    check("_format_choices" in message_source, "полные варианты выводятся в сообщении")
    check("Нажми A, B или C ниже" in message_source, "сообщение объясняет короткие кнопки")

    check("next_turn_callback" in main_source, "есть обработчик Далее")
    check("next_turn_keyboard()" in main_source, "после выбора показывается кнопка Далее")
    check("build_turn_message(current_turn, game)" in main_source, "следующий ход показывается только после Далее")

    print()
    print("UI flow checks passed.")


if __name__ == "__main__":
    main()
