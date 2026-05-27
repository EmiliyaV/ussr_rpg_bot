from pathlib import Path
import json
import inspect
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from app.content.history import HISTORY_DATA_PATH, HISTORY_TURNS, get_context_word_counts
from app.game.rules import MIN_YEAR_CONTEXT_WORDS
from app.llm.ollama_client import OllamaClient
from app.storage.repository import SqliteGameRepository
from app.game.engine import GameEngine


def check(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit("[FAIL] " + message)
    print("[OK] " + message)


def main() -> None:
    data = json.loads(HISTORY_DATA_PATH.read_text(encoding="utf-8"))

    for item in data:
        year = int(item["year"])
        focus = item["historical_focus"]

        check("Дополнительный исторический слой года:" not in focus, f"{year}: old repeated focus block removed")
        check(len(item.get("real_fact_sources", [])) > 0, f"{year}: fact source ids configured")

        source_ids = {source["id"] for source in item["sources"]}
        for fact in item["real_fact_sources"]:
            check(bool(fact.get("source_ids")), f"{year}: fact has source_ids")
            check(set(fact["source_ids"]).issubset(source_ids), f"{year}: fact source_ids point to sources")

        check(
            get_context_word_counts()[year] >= MIN_YEAR_CONTEXT_WORDS,
            f"{year}: historical_focus keeps minimum length",
        )

    by_year = {int(item["year"]): item for item in data}

    check("Украин" in by_year[1932]["historical_focus"], "1932: Ukraine regionality added")
    check("Казахстан" in by_year[1932]["historical_focus"], "1932: Kazakhstan regionality added")
    check("Северн" in by_year[1933]["historical_focus"], "1933: North Caucasus regionality added")
    check("Западную Украину" in by_year[1939]["historical_focus"], "1939: Western Ukraine regionality added")
    check("Карельскому перешейку" in by_year[1939]["historical_focus"], "1939: Finnish war regionality added")

    ollama_source = inspect.getsource(OllamaClient)
    check("logger.warning" in ollama_source and "validation.reason" in ollama_source, "LLM rejection reason is logged")

    repo_source = inspect.getsource(SqliteGameRepository.save_game)
    check("expected_turn" in repo_source, "repository save_game accepts expected_turn")
    check("WHERE user_id = ?" in repo_source and "AND turn = ?" in repo_source, "SQLite optimistic update checks turn")

    engine_source = inspect.getsource(GameEngine.apply_choice)
    check("expected_turn = state.turn" in engine_source, "engine remembers turn before applying choice")
    check("expected_turn=expected_turn" in engine_source, "engine saves with expected_turn")

    for turn in HISTORY_TURNS:
        check(bool(turn.fact_sources), f"{turn.year}: fact_sources available in HistoryTurn")

    print("Historical quality patch checks passed.")


if __name__ == "__main__":
    main()
