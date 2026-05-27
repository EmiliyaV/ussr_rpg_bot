from __future__ import annotations

from copy import deepcopy

from app.content.history import get_history_turn, get_total_turns
from app.content.roles import ROLES
from app.domain.models import ApplyChoiceResult, ChoiceDefinition, GameState, HistoryTurn
from app.game.consequence_interpreter import interpret_effects
from app.game.fallback_narrator import build_final_fallback, build_year_result_fallback
from app.game.outcome_resolver import OutcomeResolver, YearOutcome
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
        self._outcome_resolver = OutcomeResolver()

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
            tags=[],
            major_events=[],
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

        expected_turn = state.turn

        history_turn = get_history_turn(state.turn)

        if history_turn is None:
            raise RuntimeError("Current turn was not found")

        role = ROLES[state.role_id]
        choice = self._find_choice(history_turn, choice_id)

        stats_before = deepcopy(state.stats)
        tags_before = list(state.tags)
        major_events_before = list(state.major_events)

        new_stats = self._apply_effects(state.stats, choice.effects)
        choice_effect_meanings = interpret_effects(choice.effects)

        tags_after_choice = self._merge_tags(state.tags, choice.tags)

        outcome = self._outcome_resolver.resolve(
            history_turn=history_turn,
            role=role,
            choice=choice,
            stats_before=stats_before,
            stats_after_choice=new_stats,
            tags_before=tags_before,
            tags_after_choice=tags_after_choice,
            major_events=major_events_before,
        )

        outcome_effect_meanings: list[str] = []
        if outcome.extra_effects:
            new_stats = self._apply_effects(new_stats, outcome.extra_effects)
            outcome_effect_meanings = interpret_effects(outcome.extra_effects)

        effect_meanings = [*choice_effect_meanings, *outcome_effect_meanings]

        state.stats = new_stats
        state.tags = self._merge_tags(tags_after_choice, outcome.tags)
        state.major_events = [
            *state.major_events,
            self._build_major_event_line(
                history_turn=history_turn,
                choice=choice,
                outcome=outcome,
                effect_meanings=effect_meanings,
            ),
        ]
        state.memory = [
            *state.memory,
            self._build_memory_line(
                history_turn=history_turn,
                choice=choice,
                outcome=outcome,
                effect_meanings=effect_meanings,
            ),
        ]

        self._update_state_after_choice(state)

        state_description = describe_state(new_stats)

        generated_year_result = await self._llm_client.generate_year_result(
            history_turn=history_turn,
            role=role,
            choice=choice,
            outcome=outcome,
            effect_meanings=effect_meanings,
            state_description=state_description,
            memory=state.memory,
            major_events=state.major_events,
        )

        year_result_text = generated_year_result or build_year_result_fallback(
            history_turn=history_turn,
            role=role,
            choice=choice,
            outcome=outcome,
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
                major_events=state.major_events,
                ending_type=ending_type,
            )

            final_text = generated_final or build_final_fallback(
                role=role,
                ending_type=ending_type,
                state_description=final_state_description,
                major_events=state.major_events,
            )

        saved = self._repository.save_game(state, expected_turn=expected_turn)
        if not saved:
            raise RuntimeError("Этот ход уже был обработан. Нажми актуальную кнопку в последнем сообщении.")

        return ApplyChoiceResult(
            year_result_text=year_result_text,
            final_text=final_text,
            state=state,
        )

    def _merge_tags(self, current_tags: list[str], new_tags: list[str]) -> list[str]:
        result = list(current_tags)
        seen = set(result)

        for tag in new_tags:
            if tag not in seen:
                result.append(tag)
                seen.add(tag)

        return result

    def _build_memory_line(
        self,
        *,
        history_turn: HistoryTurn,
        choice: ChoiceDefinition,
        outcome: YearOutcome,
        effect_meanings: list[str],
    ) -> str:
        effect_text = "; ".join(effect_meanings)
        critical_marker = "Критическая точка года." if outcome.is_critical else "Обычный годовой исход."

        return (
            f"{history_turn.year}: выбран вариант '{choice.text}'. "
            f"{critical_marker} "
            f"Исход: {outcome.title}. "
            f"Смысл исхода: {outcome.summary}. "
            f"Последствия: {effect_text}."
        )

    def _build_major_event_line(
        self,
        *,
        history_turn: HistoryTurn,
        choice: ChoiceDefinition,
        outcome: YearOutcome,
        effect_meanings: list[str],
    ) -> str:
        if outcome.major_event:
            return outcome.major_event

        return (
            f"{history_turn.year} — {history_turn.title}: "
            f"выбор '{choice.text}'. "
            f"Исход: {outcome.title}. "
            f"Последствия: {'; '.join(effect_meanings)}."
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
        defeat_reason = self._get_defeat_reason(state.stats, state.role_id)

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

    def _get_defeat_reason(self, stats: dict[str, int], role_id: str) -> str | None:
        suspicion = stats.get("suspicion", 0)
        survival = stats.get("survival", 0)
        loyalty = stats.get("loyalty", 0)

        if suspicion >= 10:
            return "жертва подозрений"

        if survival <= -5:
            return "сломленный эпохой человек"

        # Для обычных ролей крайне низкая лояльность вместе с высоким подозрением
        # означает разоблачение как врага системы.
        #
        # Для роли traitor низкая loyalty является сутью роли, а не самостоятельным
        # условием поражения. Скрытый противник должен проигрывать не из-за самой
        # нелояльности, а из-за разоблачения: высокого подозрения и слабой защиты.
        if role_id != "traitor" and loyalty <= -8 and suspicion >= 7:
            return "скрытый враг, разоблачённый системой"

        if role_id == "traitor" and suspicion >= 9 and survival <= 1:
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
