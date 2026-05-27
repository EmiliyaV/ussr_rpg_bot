from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from app.content.history import HISTORY_DATA_PATH, HISTORY_TURNS
from app.llm.response_validator import validate_llm_response


def check(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit("[FAIL] " + message)
    print("[OK] " + message)


def main() -> None:
    check(HISTORY_DATA_PATH.exists(), "history_data.json exists")
    check(len(HISTORY_TURNS) >= 20, "loaded at least 20 turns from JSON")

    for turn in HISTORY_TURNS:
        check(bool(turn.sources), f"{turn.year}: sources configured")

        for choice in turn.choices:
            check(bool(choice.tags), f"{turn.year}{choice.id}: tags configured")
            check(len(choice.text) >= 45, f"{turn.year}{choice.id}: choice text is event-specific enough")

            if turn.year < 1937:
                suspicion = choice.effects.get("suspicion", 0)
                check(suspicion <= 3, f"{turn.year}{choice.id}: early suspicion is softened")

    bad_metrics = validate_llm_response("Итог года. suspicion +2, loyalty -1.")
    check(not bad_metrics.is_valid, "validator rejects internal metrics")

    bad_history = validate_llm_response("Ты остановил коллективизацию и отменил НЭП.")
    check(not bad_history.is_valid, "validator rejects major history rewrites")

    good = validate_llm_response("Итог 1937 года. Твои старые связи снова всплыли, и семья стала говорить тише.")
    check(good.is_valid, "validator accepts normal narrative with historical year")

    print("Data JSON migration and LLM validation checks passed.")


if __name__ == "__main__":
    main()
