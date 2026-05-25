from app.content.roles import ROLES
from app.domain.models import GameState


def _level(
    value: int,
    *,
    very_low: str,
    low: str,
    neutral: str,
    high: str,
    very_high: str,
) -> str:
    if value <= -6:
        return very_low
    if value <= -2:
        return low
    if value <= 2:
        return neutral
    if value <= 6:
        return high
    return very_high


def describe_wealth(value: int) -> str:
    return _level(
        value,
        very_low="бедственное, почти без ресурсов",
        low="тяжёлое, с постоянной нехваткой",
        neutral="скромное, без серьёзной опоры",
        high="устойчивое, с полезными запасами и связями",
        very_high="сильное, заметное для окружающих",
    )


def describe_loyalty(value: int) -> str:
    return _level(
        value,
        very_low="власть считает тебя крайне ненадёжным человеком",
        low="власть относится к тебе с сомнением",
        neutral="власть пока не видит в тебе ни опоры, ни явной угрозы",
        high="власть склонна считать тебя полезным и управляемым",
        very_high="ты выглядишь почти образцово лояльным человеком",
    )


def describe_influence(value: int) -> str:
    return _level(
        value,
        very_low="почти отсутствует, к твоему мнению не прислушиваются",
        low="слабое, твои связи ненадёжны",
        neutral="ограниченное, но иногда заметное",
        high="заметное, с возможностью влиять на решения вокруг себя",
        very_high="сильное, тебя уже воспринимают как человека с весом",
    )


def describe_suspicion(value: int) -> str:
    return _level(
        value,
        very_low="ты почти не привлекаешь опасного внимания",
        low="лишнее внимание к тебе ослабло",
        neutral="вокруг тебя есть осторожность, но без прямой угрозы",
        high="к тебе относятся с заметным подозрением",
        very_high="за тобой почти открыто присматривают",
    )


def describe_survival(value: int) -> str:
    return _level(
        value,
        very_low="твоя безопасность почти разрушена",
        low="ты держишься с трудом",
        neutral="ты пока удерживаешься на плаву",
        high="у тебя есть запас прочности",
        very_high="ты хорошо защищён обстоятельствами и связями",
    )


def describe_people_support(value: int) -> str:
    return _level(
        value,
        very_low="люди сторонятся тебя и говорят о тебе холодно",
        low="отношение людей ухудшилось",
        neutral="люди относятся к тебе с осторожной неопределённостью",
        high="часть людей видит в тебе поддержку",
        very_high="тебя уважают и готовы помнить твою помощь",
    )


def describe_state(stats: dict[str, int]) -> str:
    return "\n".join(
        [
            f"Материальное положение: {describe_wealth(stats.get('wealth', 0))}.",
            f"Отношение власти: {describe_loyalty(stats.get('loyalty', 0))}.",
            f"Влияние: {describe_influence(stats.get('influence', 0))}.",
            f"Опасность подозрения: {describe_suspicion(stats.get('suspicion', 0))}.",
            f"Личная устойчивость: {describe_survival(stats.get('survival', 0))}.",
            f"Отношение людей: {describe_people_support(stats.get('people_support', 0))}.",
        ]
    )


def describe_state_for_player(state: GameState) -> str:
    role = ROLES[state.role_id]

    status_label = {
        "active": "игра продолжается",
        "finished": "история завершена",
        "lost": "персонаж проиграл",
    }.get(state.status, state.status)

    return (
        "Текущее положение\n\n"
        f"Роль: {role.name}\n"
        f"Ход: {state.turn}\n"
        f"Статус: {status_label}\n\n"
        f"{describe_state(state.stats)}"
    )


def describe_final_state(stats: dict[str, int]) -> str:
    return describe_state(stats)
