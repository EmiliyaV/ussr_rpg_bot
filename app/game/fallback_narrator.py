from __future__ import annotations

from app.domain.models import ChoiceDefinition, HistoryTurn, RoleDefinition
from app.game.outcome_resolver import YearOutcome


def _sentence_for_meaning(meaning: str) -> str:
    if "материальное положение" in meaning and "улучшилось" in meaning:
        return "У тебя появилось больше ресурсов, но в такую эпоху лишние вещи редко остаются незамеченными."
    if "материальное положение" in meaning and "ухудшилось" in meaning:
        return "Ресурсов стало меньше, и каждое решение теперь ощущается тяжелее."

    if "власть стала" in meaning and "доверять" in meaning:
        return "Власть стала смотреть на тебя спокойнее, будто ты лучше вписался в ожидаемую линию поведения."
    if "лояльность игрока" in meaning and "сомнения" in meaning:
        return "В твоей политической надёжности стало больше сомнений, и это постепенно меняет тон разговоров вокруг тебя."

    if "личное влияние" in meaning and "выросло" in meaning:
        return "Твоё влияние выросло: появились люди, которым приходится считаться с твоим словом."
    if "личное влияние" in meaning and "ослабло" in meaning:
        return "Твоё влияние ослабло, и люди стали реже воспринимать тебя как человека, способного защитить или помочь."

    if "подозрение" in meaning and "усилилось" in meaning:
        return "Твоё имя стало чаще всплывать в настороженных разговорах, и за твоими действиями начали присматриваться внимательнее."
    if "подозрение" in meaning and "снизилось" in meaning:
        return "На время тебе удалось отвести от себя лишнее внимание, и это дало немного воздуха."

    if "личная безопасность" in meaning and "укрепилась" in meaning:
        return "Твоё положение стало безопаснее: появились люди, обстоятельства или связи, которые могут прикрыть тебя."
    if "личная безопасность" in meaning and "ухудшилась" in meaning:
        return "Твоя безопасность пошатнулась, и теперь даже обычный разговор может показаться слишком рискованным."

    if "отношение обычных людей" in meaning and "улучшилось" in meaning:
        return "Обычные люди стали относиться к тебе теплее, будто увидели в тебе не только приспособленца, но и человека."
    if "отношение обычных людей" in meaning and "ухудшилось" in meaning:
        return "Окружающие стали холоднее: в разговорах стало больше пауз, недоверия и скрытого осуждения."

    return meaning.rstrip(".") + "."


def build_year_result_fallback(
    *,
    history_turn: HistoryTurn,
    role: RoleDefinition,
    choice: ChoiceDefinition,
    outcome: YearOutcome,
    effect_meanings: list[str],
    state_description: str,
) -> str:
    details = " ".join(_sentence_for_meaning(item) for item in effect_meanings[:6])

    critical_line = ""
    if outcome.is_critical:
        critical_line = (
            "\n\nЭтот год стал для тебя не просто очередным ходом, а критической точкой: "
            "прошлые решения начали менять настоящее."
        )

    return (
        f"Итог {history_turn.year} года\n\n"
        f"Ты выбрал: {choice.text}.\n\n"
        f"{outcome.title}\n\n"
        f"{outcome.scene}.\n\n"
        f"{outcome.summary} "
        f"{outcome.public_consequence}. "
        f"{outcome.private_consequence}."
        f"{critical_line}\n\n"
        f"{details}\n\n"
        "Общее положение теперь ощущается так:\n"
        f"{state_description}"
    )


def build_final_fallback(
    *,
    role: RoleDefinition,
    ending_type: str,
    state_description: str,
    major_events: list[str] | None = None,
) -> str:
    events = major_events or []
    event_block = ""

    if events:
        visible_events = "\n".join(f"- {item}" for item in events[-8:])
        event_block = (
            "\n\nКлючевые следы твоей биографии:\n"
            f"{visible_events}"
        )

    return (
        "Финал игры\n\n"
        f"Ты завершил путь как: {ending_type}.\n\n"
        f"Роль: {role.name}\n\n"
        "К 1940 году твоя личная история стала итогом компромиссов, страха, выбора и последствий. "
        "Ты не изменил ход истории страны, но история изменила тебя и тех, кто был рядом. "
        "Одни решения дали тебе защиту, другие оставили холод в отношениях с людьми. "
        "Даже если ты выжил, твоя судьба уже несёт след прожитой эпохи."
        f"{event_block}\n\n"
        "Итоговое положение:\n"
        f"{state_description}"
    )
