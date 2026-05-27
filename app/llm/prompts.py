from __future__ import annotations

from app.domain.models import ChoiceDefinition, HistoryTurn, RoleDefinition
from app.game.context_builder import (
    build_previous_answers_context,
    build_year_context_for_llm,
    trim_to_word_limit,
)
from app.game.consequence_interpreter import format_effect_meanings
from app.game.outcome_resolver import YearOutcome


def _format_major_events(major_events: list[str] | None, max_words: int = 280) -> str:
    if not major_events:
        return "Значимых личных событий пока нет."

    raw = "\n".join(f"- {item}" for item in major_events[-10:])
    return trim_to_word_limit(raw, max_words)


def build_year_result_prompt(
    *,
    history_turn: HistoryTurn,
    role: RoleDefinition,
    choice: ChoiceDefinition,
    outcome: YearOutcome,
    effect_meanings: list[str],
    state_description: str,
    memory: list[str],
    major_events: list[str] | None = None,
) -> str:
    year_context = build_year_context_for_llm(history_turn)
    previous_context = build_previous_answers_context(memory, max_words=350)
    effect_text = format_effect_meanings(effect_meanings)
    major_events_context = _format_major_events(major_events)
    choice_tags = ", ".join(choice.tags) if choice.tags else "нет специальных сюжетных следов"

    critical_instruction = (
        "Это критический год. Итог должен явно ощущаться как поворотная точка личной биографии: "
        "прошлые решения могут вернуться, а последствия должны влиять на дальнейшую судьбу."
        if outcome.is_critical
        else
        "Это не главный исторический перелом, но итог всё равно должен оставлять личный след."
    )

    return (
        "Ты — рассказчик интерактивной исторической игры «Красная развилка».\n"
        "Твоя задача — написать художественный итог года от второго лица, обращаясь к игроку на «ты».\n\n"
        "Строгие правила:\n"
        "- не показывай числовые метрики;\n"
        "- не пересчитывай показатели;\n"
        "- не показывай числовые значения и внутренние метрики;\n"
        "- не пиши названия внутренних метрик: wealth, loyalty, influence, suspicion, survival, people_support;\n"
        "- не выводи технические теги дословно;\n"
        "- не называй outcome_type, severity, tags и другие служебные поля;\n"
        "- не меняй крупные исторические события;\n"
        "- не делай игрока руководителем всей страны;\n"
        "- не отменяй НЭП, образование СССР, индустриализацию, коллективизацию, террор или начало войны;\n"
        "- не превращай трагические события в приключенческий успех;\n"
        "- не перечисляй весь исторический контекст как лекцию;\n"
        "- используй исторический контекст только как основу для личной драмы;\n"
        "- итог должен быть разнообразным, конкретным и связанным с выбором;\n"
        "- можно писать длиннее прежнего, но не больше 1000 слов.\n\n"
        "Исторический контекст года:\n"
        f"{year_context}\n\n"
        "Роль игрока:\n"
        f"{role.name}\n"
        f"{role.description}\n\n"
        "Выбор игрока:\n"
        f"{choice.text}\n\n"
        "Сюжетные следы выбора для внутренней драматургии:\n"
        f"{choice_tags}\n\n"
        "Механически рассчитанные последствия, которые надо выразить художественно без чисел:\n"
        f"{effect_text}\n\n"
        "Исход года, рассчитанный кодом. Его нужно использовать как главный каркас текста:\n"
        f"{outcome.to_prompt_block()}\n\n"
        "Важное указание по силе года:\n"
        f"{critical_instruction}\n\n"
        "Краткий контекст предыдущих решений:\n"
        f"{previous_context}\n\n"
        "Ключевые следы личной биографии игрока:\n"
        f"{major_events_context}\n\n"
        "Текущее положение игрока после выбора, уже переведённое в человеческие описания:\n"
        f"{state_description}\n\n"
        "Формат ответа:\n"
        f"Итог {history_turn.year} года\n\n"
        "Далее 2–6 абзацев художественного текста. "
        "Если год критический, покажи, почему он стал поворотным. "
        "Если в прошлых решениях есть подходящие следы, аккуратно свяжи с ними итог. "
        "Не используй списки, таблицы и технические подписи."
    )


def build_final_prompt(
    *,
    role: RoleDefinition,
    state_description: str,
    memory: list[str],
    major_events: list[str] | None,
    ending_type: str,
) -> str:
    previous_context = build_previous_answers_context(memory, max_words=550)
    major_events_context = _format_major_events(major_events, max_words=450)

    return (
        "Ты — рассказчик интерактивной исторической игры «Красная развилка».\n"
        "Нужно написать финал личной судьбы игрока к 1940 году.\n\n"
        "Строгие правила:\n"
        "- не показывай числовые значения и внутренние метрики;\n"
        "- не пиши названия внутренних метрик;\n"
        "- не выводи технические теги и служебные типы исходов;\n"
        "- не меняй крупную историю СССР и Европы;\n"
        "- игрок не должен становиться главным архитектором истории страны;\n"
        "- финал должен вытекать из накопленной биографии, а не только из последнего года;\n"
        "- можно писать длиннее прежнего, но не больше 1000 слов.\n\n"
        "Роль игрока:\n"
        f"{role.name}\n"
        f"{role.description}\n\n"
        "Тип финала, рассчитанный кодом:\n"
        f"{ending_type}\n\n"
        "Предыдущие решения игрока:\n"
        f"{previous_context}\n\n"
        "Ключевые следы биографии:\n"
        f"{major_events_context}\n\n"
        "Итоговое положение игрока, уже переведённое в человеческие описания:\n"
        f"{state_description}\n\n"
        "Формат ответа:\n"
        "Финал игры\n\n"
        "Далее 3–7 абзацев. Нужно показать судьбу игрока к 1940 году: "
        "кто рядом с ним остался, кто отвернулся, чего он добился, чего лишился, "
        "какую цену заплатил и почему именно такой финал получился. "
        "Не используй списки, таблицы и технические подписи."
    )
