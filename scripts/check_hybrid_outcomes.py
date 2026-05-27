from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from app.content.history import HISTORY_TURNS
from app.content.roles import ROLES
from app.game.outcome_resolver import CRITICAL_YEARS, OutcomeResolver


def check(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def main() -> None:
    resolver = OutcomeResolver()
    turns_by_year = {turn.year: turn for turn in HISTORY_TURNS}

    check(CRITICAL_YEARS == {1921, 1929, 1930, 1932, 1934, 1937, 1938, 1939}, "Unexpected critical years set.")
    check(all(year in turns_by_year for year in CRITICAL_YEARS), "Some critical years are missing in HISTORY_TURNS.")

    role = ROLES["opportunist"]

    for year in sorted(CRITICAL_YEARS):
        turn = turns_by_year[year]
        choice = turn.choices[0]
        outcome = resolver.resolve(
            history_turn=turn,
            role=role,
            choice=choice,
            stats_before={
                "wealth": 4,
                "loyalty": 1,
                "influence": 1,
                "suspicion": 1,
                "survival": 4,
                "people_support": 1,
            },
            stats_after_choice={
                "wealth": 5,
                "loyalty": 2,
                "influence": 2,
                "suspicion": 2,
                "survival": 4,
                "people_support": 1,
            },
            tags_before=[],
            tags_after_choice=list(choice.tags),
            major_events=[],
        )
        check(outcome.is_critical, f"{year} should be critical.")
        check(outcome.title, f"{year} outcome has no title.")
        check(outcome.scene, f"{year} outcome has no scene.")
        check(outcome.major_event, f"{year} outcome has no major_event.")

    non_critical_turn = turns_by_year[1920]
    non_critical_choice = non_critical_turn.choices[0]
    non_critical_outcome = resolver.resolve(
        history_turn=non_critical_turn,
        role=role,
        choice=non_critical_choice,
        stats_before={
            "wealth": 4,
            "loyalty": 1,
            "influence": 1,
            "suspicion": 1,
            "survival": 4,
            "people_support": 1,
        },
        stats_after_choice={
            "wealth": 3,
            "loyalty": 3,
            "influence": 2,
            "suspicion": 0,
            "survival": 4,
            "people_support": 1,
        },
        tags_before=[],
        tags_after_choice=list(non_critical_choice.tags),
        major_events=[],
    )
    check(not non_critical_outcome.is_critical, "1920 should not be critical in this step.")

    print("Hybrid outcome checks passed.")


if __name__ == "__main__":
    main()
