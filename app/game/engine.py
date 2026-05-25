from copy import deepcopy

from app.content.history import get_history_turn, get_total_turns
from app.content.roles import ROLES
from app.domain.models import ApplyChoiceResult, ChoiceDefinition, GameState, HistoryTurn
from app.game.consequence_interpreter import interpret_effects
from app.game.fallback_narrator import build_final_fallback, build_year_result_fallback
from app.game.rules import MAX_STAT_VALUE, MIN_STAT_VALUE
from app.game.stat_interpreter import describe_final_state, describe_state
from app.llm.ollama_client import OllamaClient
from app.storage.repository import SqliteGameRepository


class GameEngine:
    def __init__(
        self,
        *,
        repository: SqliteGameRepository,
        llm_client: OllamaClient,
    ) -> None:
        self._repository = repository
        self._llm_client = llm_client

    def start_game(self, user_id: int, role_id: str) -> GameState:
        if role_id not in ROLES:
            raise ValueError(f"Unknown role: {role_id}")

        role = ROLES[role_id]
        state = GameState(
            user_id=user_id,
            role_id=role_id,
            turn=1,
            stats=deepcopy(role.initial_stats),
            memory=[],
            status="active",
            ending_type=None,
        )
        self._repository.save_game(state)
        return state

    def restart_game(self, user_id: int) -> None:
        self._repository.delete_game(user_id)

    def get_game(self, user_id: int) -> GameState | None:
        return self._repository.get_game(user_id)

    def get_current_turn(self, state: GameState) -> HistoryTurn | None:
        if state.status != "active":
            return None

        return get_history_turn(state.turn)

    async def apply_choice(self, user_id: int, choice_id: str) -> ApplyChoiceResult:
        state = self._repository.get_game(user_id)

        if state is None:
            raise RuntimeError("Game is not started")

        if state.status != "active":
            raise RuntimeError("Game is already finished")

        history_turn = get_history_turn(state.turn)

        if history_turn is None:
            raise RuntimeError("Current turn was not found")

        choice = self._find_choice(history_turn, choice_id)
        new_stats = self._apply_effects(state.stats, choice.effects)
        effect_meanings = interpret_effects(choice.effects)

        memory_line = (
            f"{history_turn.year}: выбран вариант '{choice.text}'. "
            f"Смысл последствий: {', '.join(effect_meanings)}."
        )

        state.stats = new_stats
        state.memory = [*state.memory, memory_line]

        self._update_state_after_choice(state)

        role = ROLES[state.role_id]
        state_description = describe_state(new_stats)

        generated_year_result = await self._llm_client.generate_year_result(
            history_turn=history_turn,
            role=role,
            choice=choice,
            effect_meanings=effect_meanings,
            state_description=state_description,
            memory=state.memory,
        )

        year_result_text = generated_year_result or build_year_result_fallback(
            history_turn=history_turn,
            role=role,
            choice=choice,
            effect_meanings=effect_meanings,
            state_description=state_description,
        )

        final_text = None

        if state.status in {"finished", "lost"}:
            ending_type = state.ending_type or self._determine_ending_type(state.stats)
            final_state_description = describe_final_state(state.stats)

            generated_final = await self._llm_client.generate_final(
                role=role,
                state_description=final_state_description,
                memory=state.memory,
                ending_type=ending_type,
            )

            final_text = generated_final or build_final_fallback(
                role=role,
                ending_type=ending_type,
                state_description=final_state_description,
            )

        self._repository.save_game(state)

        return ApplyChoiceResult(
            year_result_text=year_result_text,
            final_text=final_text,
            state=state,
        )

    def _find_choice(self, history_turn: HistoryTurn, choice_id: str) -> ChoiceDefinition:
        normalized_id = choice_id.strip().upper()

        for choice in history_turn.choices:
            if choice.id == normalized_id:
                return choice

        raise ValueError(f"Unknown choice: {choice_id}")

    def _apply_effects(
        self,
        stats: dict[str, int],
        effects: dict[str, int],
    ) -> dict[str, int]:
        new_stats = deepcopy(stats)

        for key, delta in effects.items():
            old_value = new_stats.get(key, 0)
            new_value = old_value + delta
            new_stats[key] = max(MIN_STAT_VALUE, min(MAX_STAT_VALUE, new_value))

        return new_stats

    def _update_state_after_choice(self, state: GameState) -> None:
        defeat_reason = self._get_defeat_reason(state.stats)

        if defeat_reason is not None:
            state.status = "lost"
            state.ending_type = defeat_reason
            return

        if state.turn >= get_total_turns():
            state.status = "finished"
            state.ending_type = self._determine_ending_type(state.stats)
            return

        state.turn += 1
        state.status = "active"
        state.ending_type = None

    def _get_defeat_reason(self, stats: dict[str, int]) -> str | None:
        if stats.get("suspicion", 0) >= 10:
            return "жертва подозрений"

        if stats.get("survival", 0) <= -5:
            return "сломленный эпохой человек"

        if stats.get("loyalty", 0) <= -8 and stats.get("suspicion", 0) >= 7:
            return "скрытый враг, разоблачённый системой"

        return None

    def _determine_ending_type(self, stats: dict[str, int]) -> str:
        if stats.get("suspicion", 0) >= 8:
            return "жертва подозрений"

        if stats.get("loyalty", 0) >= 7 and stats.get("influence", 0) >= 5:
            return "партийный карьерист"

        if stats.get("wealth", 0) >= 7 and stats.get("suspicion", 0) <= 5:
            return "выживший приспособленец"

        if stats.get("people_support", 0) >= 6:
            return "человек, помогавший другим"

        if stats.get("loyalty", 0) <= -6:
            return "скрытый враг, не сумевший изменить систему"

        if stats.get("survival", 0) <= 0:
            return "сломленный эпохой человек"

        return "обычный выживший в тяжёлой эпохе"
