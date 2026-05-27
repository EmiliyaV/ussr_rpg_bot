from dataclasses import dataclass, field
from typing import Any, Literal


StatName = Literal[
    "wealth",
    "loyalty",
    "influence",
    "suspicion",
    "survival",
    "people_support",
]

GameStatus = Literal["active", "finished", "lost"]


@dataclass(frozen=True)
class RoleDefinition:
    id: str
    name: str
    description: str
    initial_stats: dict[str, int]


@dataclass(frozen=True)
class ChoiceDefinition:
    id: str
    text: str
    effects: dict[str, int]
    tags: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class HistoryTurn:
    turn: int
    year: int
    title: str
    context: str
    immutable_facts: list[str]
    question: str
    choices: list[ChoiceDefinition]
    real_facts: list[str] = field(default_factory=list)
    player_limits: list[str] = field(default_factory=list)
    sources: list[dict[str, str]] = field(default_factory=list)
    fact_sources: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class GameState:
    user_id: int
    role_id: str
    turn: int
    stats: dict[str, int]
    memory: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    major_events: list[str] = field(default_factory=list)
    status: GameStatus = "active"
    ending_type: str | None = None


@dataclass(frozen=True)
class ApplyChoiceResult:
    year_result_text: str
    final_text: str | None
    state: GameState
