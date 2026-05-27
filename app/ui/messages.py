import re
import textwrap

from app.content.roles import ROLES
from app.domain.models import GameState, HistoryTurn, RoleDefinition
from app.game.stat_interpreter import describe_state_for_player


def _normalize_text(text: str) -> str:
    prepared = textwrap.dedent(text).replace("\t", " ")
    raw_lines = prepared.splitlines()

    paragraphs: list[str] = []
    current: list[str] = []

    for raw_line in raw_lines:
        line = re.sub(r"\s+", " ", raw_line.strip())

        if not line:
            if current:
                paragraphs.append(" ".join(current))
                current = []
            continue

        current.append(line)

    if current:
        paragraphs.append(" ".join(current))

    return "\n\n".join(paragraphs).strip()


def _shorten(text: str, limit: int) -> str:
    normalized = _normalize_text(text)

    if len(normalized) <= limit:
        return normalized

    cut = normalized[:limit].rstrip()
    last_dot = max(cut.rfind("."), cut.rfind("!"), cut.rfind("?"))

    if last_dot > limit * 0.55:
        return cut[: last_dot + 1]

    return cut + "..."


def _extract_short_context(context: str, limit: int = 900) -> str:
    cleaned = _normalize_text(context)

    marker = "Исторический фокус года:"
    if marker in cleaned:
        after_marker = cleaned.split(marker, maxsplit=1)[1].strip()
        stop_markers = [
            "Неизменяемые факты:",
            "Ракурс для трёх ролей:",
            "Разрешённые типы локальных последствий:",
            "Игровая рамка этого проекта",
        ]

        for stop_marker in stop_markers:
            if stop_marker in after_marker:
                after_marker = after_marker.split(stop_marker, maxsplit=1)[0].strip()

        return _shorten(after_marker, limit)

    return _shorten(cleaned, limit)


def _format_real_facts(history_turn: HistoryTurn) -> str:
    facts = getattr(history_turn, "real_facts", None) or history_turn.immutable_facts
    return "\n".join(f"— {_normalize_text(fact)}" for fact in facts)


def _format_player_limits(history_turn: HistoryTurn) -> str:
    limits = getattr(history_turn, "player_limits", None) or []
    if not limits:
        limits = [fact for fact in history_turn.immutable_facts if fact.startswith("Игрок не может")]
    return "\n".join(f"— {_normalize_text(fact)}" for fact in limits)


def _format_immutable_facts(history_turn: HistoryTurn) -> str:
    return "\n".join(f"— {_normalize_text(fact)}" for fact in history_turn.immutable_facts)


def _format_choices(history_turn: HistoryTurn) -> str:
    lines = []

    for choice in history_turn.choices:
        lines.append(f"{choice.id}. {_normalize_text(choice.text)}")

    return "\n".join(lines)


def intro_message() -> str:
    return (
        "СССР: 20 вопросов\n\n"
        "Историческая ролевая игра в Telegram.\n"
        "Ты выбираешь роль и проходишь 20 ходов: с 1920 по 1939 год. "
        "К 1940 году игра подводит итог твоей личной судьбы.\n\n"
        "Выбери роль:"
    )


def help_message() -> str:
    return (
        "Команды:\n"
        "/start — начать новую игру\n"
        "/status — показать текущее положение без чисел\n"
        "/debug_status — показать скрытые числа для отладки, только если DEBUG_COMMANDS_ENABLED=true\n"
        "/help — справка\n\n"
        "Правила:\n"
        "- крупные события СССР нельзя отменить одним выбором;\n"
        "- выбор влияет на личную судьбу персонажа;\n"
        "- внутренние метрики считает код;\n"
        "- Ollama используется только для атмосферного текста последствий;\n"
        "- после итога года нужно нажать «Далее», чтобы перейти к следующему ходу."
    )


def role_selected_message(role: RoleDefinition) -> str:
    return (
        f"Роль выбрана: {role.name}\n\n"
        f"{_normalize_text(role.description)}\n\n"
        "Игра начинается."
    )


def build_turn_message(history_turn: HistoryTurn, state: GameState) -> str:
    role = ROLES[state.role_id]
    short_context = _extract_short_context(history_turn.context)
    real_facts = _format_real_facts(history_turn)
    player_limits = _format_player_limits(history_turn)
    choices = _format_choices(history_turn)

    return (
        f"Ход {history_turn.turn}/20. {history_turn.year} год\n"
        f"{_normalize_text(history_turn.title)}\n\n"
        f"Роль: {role.name}\n\n"
        f"Краткий контекст:\n"
        f"{short_context}\n\n"
        f"Реальные факты года:\n"
        f"{real_facts}\n\n"
        f"Что нельзя изменить:\n"
        f"{player_limits}\n\n"
        f"Вопрос:\n"
        f"{_normalize_text(history_turn.question)}\n\n"
        f"Варианты:\n"
        f"{choices}\n\n"
        "Нажми A, B или C ниже."
    )


def build_status_message(state: GameState) -> str:
    return describe_state_for_player(state)


def build_debug_status_message(state: GameState) -> str:
    role = ROLES[state.role_id]
    lines = [f"{key}: {value}" for key, value in state.stats.items()]

    return (
        "DEBUG STATUS\n\n"
        f"Роль: {role.name}\n"
        f"Ход: {state.turn}\n"
        f"Статус: {state.status}\n"
        f"ending_type: {state.ending_type}\n\n"
        "Скрытые показатели:\n"
        + "\n".join(lines)
    )
