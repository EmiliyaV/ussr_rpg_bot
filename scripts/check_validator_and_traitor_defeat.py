from pathlib import Path
import inspect
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from app.llm.response_validator import validate_llm_response
from app.game.engine import GameEngine


def check(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit("[FAIL] " + message)
    print("[OK] " + message)


def main() -> None:
    check(
        validate_llm_response("В 1939 году пакт Молотова — Риббентропа изменил официальную риторику.").is_valid,
        "validator allows normal Molotov-Ribbentrop pact mention",
    )

    check(
        validate_llm_response("7 августа 1932 года распоряжение стало для тебя личным испытанием.").is_valid,
        "validator allows normal historical dates",
    )

    check(
        not validate_llm_response("Итог года: suspicion +2, loyalty -1.").is_valid,
        "validator rejects internal metrics and numeric deltas",
    )

    check(
        not validate_llm_response("Твоё положение стало 10/10 безопасным.").is_valid,
        "validator rejects rating-like numeric forms",
    )

    check(
        not validate_llm_response("Ты отменил коллективизацию и остановил Большой террор.").is_valid,
        "validator rejects major history rewrite",
    )

    source = inspect.getsource(GameEngine._get_defeat_reason)
    check("role_id" in source, "defeat check is role-aware")
    check("role_id != \"traitor\"" in source, "low loyalty defeat does not apply to traitor role")

    print("Validator and traitor defeat checks passed.")


if __name__ == "__main__":
    main()
