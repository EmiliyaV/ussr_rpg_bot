from app.domain.models import ChoiceDefinition, HistoryTurn, RoleDefinition
from app.game.context_builder import (
    build_previous_answers_context,
    build_year_context_for_llm,
)
from app.game.consequence_interpreter import format_effect_meanings


def build_year_result_prompt(
    *,
    history_turn: HistoryTurn,
    role: RoleDefinition,
    choice: ChoiceDefinition,
    effect_meanings: list[str],
    state_description: str,
    memory: list[str],
) -> str:
    year_context = build_year_context_for_llm(history_turn)
    previous_context = build_previous_answers_context(memory)
    effect_text = format_effect_meanings(effect_meanings)

    return (
        "Ты — рассказчик исторической ролевой игры про СССР 1920–1940.\n\n"
        "Твоя задача — написать итог года после выбора игрока.\n\n"
        "Строгие правила:\n"
        "- не показывай числовые метрики;\n"
        "- не пиши названия внутренних метрик: wealth, loyalty, influence, suspicion, survival, people_support;\n"
        "- не пиши формулы вида '+2', '-1', 'показатель вырос';\n"
        "- не пересчитывай показатели;\n"
        "- не спорь со смыслом последствий;\n"
        "- не меняй историю СССР;\n"
        "- не утверждай, что игрок изменил ход истории страны;\n"
        "- описывай только личные, локальные и социальные последствия выбора;\n"
        "- используй исторический контекст года;\n"
        "- учитывай роль игрока;\n"
        "- учитывай краткий контекст предыдущих решений;\n"
        "- пиши 3–5 предложений;\n"
        "- стиль: мрачная историческая ролевая игра;\n"
        "- пиши по-русски.\n\n"
        f"Год:\n{history_turn.year}\n\n"
        f"Название года:\n{history_turn.title}\n\n"
        f"Большой исторический контекст года:\n{year_context}\n\n"
        f"Роль игрока:\n{role.name}\n{role.description}\n\n"
        f"Выбор игрока:\n{choice.text}\n\n"
        f"Смысл последствий выбора:\n{effect_text}\n\n"
        f"Текущее положение после выбора:\n{state_description}\n\n"
        f"Краткий контекст предыдущих решений, не больше примерно 100 слов:\n{previous_context}\n\n"
        "Напиши итог года так, чтобы игрок понял последствия выбора без чисел и технических терминов."
    )


def build_final_prompt(
    *,
    role: RoleDefinition,
    state_description: str,
    memory: list[str],
    ending_type: str,
) -> str:
    previous_context = build_previous_answers_context(memory)

    return (
        "Ты — рассказчик исторической ролевой игры про СССР 1920–1940.\n\n"
        "Сгенерируй финал судьбы персонажа.\n\n"
        "Строгие правила:\n"
        "- не показывай числовые метрики;\n"
        "- не пиши названия внутренних метрик;\n"
        "- не меняй реальные исторические события;\n"
        "- не делай игрока человеком, который изменил судьбу СССР;\n"
        "- оцени только личную судьбу персонажа;\n"
        "- учитывай роль, итоговое положение и прошлые решения;\n"
        "- текст 6–8 предложений;\n"
        "- стиль: историческая драма;\n"
        "- пиши по-русски.\n\n"
        f"Роль:\n{role.name}\n{role.description}\n\n"
        f"Итоговое положение персонажа:\n{state_description}\n\n"
        f"Краткий контекст прошлых решений, не больше примерно 100 слов:\n{previous_context}\n\n"
        f"Итоговая классификация:\n{ending_type}\n\n"
        "Напиши финал игры как личную судьбу персонажа к 1940 году."
    )
