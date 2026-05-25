from app.domain.models import ChoiceDefinition, HistoryTurn, RoleDefinition


def _sentence_for_meaning(meaning: str) -> str:
    if "материальное положение" in meaning and "улучшилось" in meaning:
        return "У тебя появилось больше ресурсов, но окружающие быстро заметили, что ты оказался в лучшем положении, чем многие другие."
    if "материальное положение" in meaning and "ухудшилось" in meaning:
        return "Твоё материальное положение стало тяжелее, и каждый следующий шаг теперь требует большей осторожности."

    if "власть" in meaning and "больше доверять" in meaning:
        return "Местная власть стала смотреть на тебя спокойнее, будто ты доказал готовность следовать её линии."
    if "лояльность" in meaning and "сомнения" in meaning:
        return "Вокруг твоей политической надёжности появились сомнения, которые в такие годы редко исчезают сами."

    if "личное влияние" in meaning and "выросло" in meaning:
        return "Твои слова и просьбы стали иметь больший вес, а некоторые люди начали искать с тобой связи."
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
    effect_meanings: list[str],
    state_description: str,
) -> str:
    details = " ".join(_sentence_for_meaning(item) for item in effect_meanings[:4])

    return (
        f"Итог {history_turn.year} года\n\n"
        f"Ты выбрал: {choice.text}.\n\n"
        f"{details}\n\n"
        "Общее положение теперь ощущается так:\n"
        f"{state_description}"
    )


def build_final_fallback(
    *,
    role: RoleDefinition,
    ending_type: str,
    state_description: str,
) -> str:
    return (
        "Финал игры\n\n"
        f"Ты завершил путь как: {ending_type}.\n\n"
        f"Роль: {role.name}\n\n"
        "К 1940 году твоя личная история стала итогом компромиссов, страха, выбора и последствий. "
        "Ты не изменил ход истории страны, но история изменила тебя и тех, кто был рядом. "
        "Одни решения дали тебе защиту, другие оставили холод в отношениях с людьми. "
        "Даже если ты выжил, твоя судьба уже несёт след прожитой эпохи.\n\n"
        "Итоговое положение:\n"
        f"{state_description}"
    )
