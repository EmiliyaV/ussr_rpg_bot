from pathlib import Path
import inspect
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from app.content.history import HISTORY_TURNS, get_total_turns
from app.content.roles import ROLES
from app.game.rules import ALLOWED_STAT_NAMES, MAX_STAT_VALUE, MIN_STAT_VALUE, REQUIRED_TOTAL_TURNS
from app.game.consequence_interpreter import interpret_effects
from app.game.stat_interpreter import describe_state
from app.game.fallback_narrator import build_final_fallback, build_year_result_fallback
from app.game.engine import GameEngine
from app.llm import prompts
from app.ui import messages


def check(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit("[FAIL] " + message)
    print("[OK] " + message)


def main() -> None:
    check(len(ROLES) == 3, "есть 3 роли")

    for role_id, role in ROLES.items():
        check(
            set(role.initial_stats.keys()) == ALLOWED_STAT_NAMES,
            f"роль {role_id} содержит 6 скрытых статов",
        )

    check(get_total_turns() >= REQUIRED_TOTAL_TURNS, "есть минимум 20 ходов")

    for turn in HISTORY_TURNS:
        check(len(turn.choices) == 3, f"{turn.year}: есть 3 варианта выбора")

        for choice in turn.choices:
            check(choice.id in {"A", "B", "C"}, f"{turn.year}: вариант {choice.id} имеет корректный id")
            check(
                set(choice.effects.keys()).issubset(ALLOWED_STAT_NAMES),
                f"{turn.year}: эффекты варианта {choice.id} используют только разрешённые статы",
            )

    sample_effects = {
        "wealth": 2,
        "suspicion": 2,
        "people_support": -1,
    }
    meanings = interpret_effects(sample_effects)
    check(isinstance(meanings, list) and meanings, "интерпретатор эффектов возвращает список последствий")
    check(not any("wealth" in item or "suspicion" in item for item in meanings), "интерпретатор не отдаёт технические имена метрик")

    state_text = describe_state(
        {
            "wealth": 4,
            "loyalty": 1,
            "influence": 0,
            "suspicion": 6,
            "survival": 3,
            "people_support": -2,
        }
    )
    check("wealth" not in state_text and "suspicion" not in state_text, "описание состояния не показывает технические имена метрик")
    check("+2" not in state_text and "-1" not in state_text, "описание состояния не показывает числовые изменения")

    engine_source = inspect.getsource(GameEngine)
    check("_apply_effects" in engine_source, "в engine.py есть пересчёт статов")
    check("max(MIN_STAT_VALUE, min(MAX_STAT_VALUE" in engine_source, "пересчёт статов ограничен диапазоном -10..10")
    check("generate_year_result" in engine_source, "engine вызывает Ollama только для итогов года")
    check("generate_final" in engine_source, "engine вызывает Ollama для финала")
    check("build_year_result_fallback" in engine_source, "engine использует fallback без Ollama")
    check("debug_status" in inspect.getsource(messages) or "DEBUG STATUS" in inspect.getsource(messages), "есть debug_status для скрытых чисел")

    prompt_source = inspect.getsource(prompts)
    check("не показывай числовые метрики" in prompt_source, "prompt запрещает показывать числа")
    check("не пересчитывай показатели" in prompt_source, "prompt запрещает пересчитывать показатели")
    check("исторический контекст" in prompt_source or "контекст года" in prompt_source, "prompt получает исторический контекст")
    check("Краткий контекст предыдущих решений" in prompt_source, "prompt получает память прошлых решений")

    fallback_source = inspect.getsource(build_year_result_fallback) + inspect.getsource(build_final_fallback)
    check("wealth" not in fallback_source and "suspicion" not in fallback_source, "fallback не показывает технические названия метрик")
    check("+2" not in fallback_source and "-1" not in fallback_source, "fallback не показывает числовые эффекты")

    check(MIN_STAT_VALUE == -10 and MAX_STAT_VALUE == 10, "диапазон статов зафиксирован как -10..10")

    print()
    print("All MVP architecture checks passed.")


if __name__ == "__main__":
    main()
