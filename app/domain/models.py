from dataclasses import dataclass, field
from typing import Literal


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


@dataclass(frozen=True)
class HistoryTurn:
    turn: int
    year: int
    title: str
    context: str
    immutable_facts: list[str]
    question: str
    choices: list[ChoiceDefinition]


@dataclass
class GameState:
    user_id: int
    role_id: str
    turn: int
    stats: dict[str, int]
    memory: list[str] = field(default_factory=list)
    status: GameStatus = "active"
    ending_type: str | None = None


@dataclass(frozen=True)
class ApplyChoiceResult:
    year_result_text: str
    final_text: str | None
    state: GameState
