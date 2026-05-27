from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from app.domain.models import ChoiceDefinition, HistoryTurn
from app.game.rules import MIN_YEAR_CONTEXT_WORDS


WORD_RE = re.compile(r"[A-Za-zА-Яа-яЁё0-9]+(?:-[A-Za-zА-Яа-яЁё0-9]+)?")

HISTORY_DATA_PATH = Path(__file__).with_name("history_data.json")

COMMON_LLM_CONTEXT_BLOCK = """Игровая рамка этого проекта устроена так, что исторический год является не свободной
фантазией, а жёсткой сценой, внутри которой игрок принимает личные решения. LLM должна
использовать этот контекст как основу для описания атмосферы, последствий выбора и
внутреннего давления эпохи. Модель может придумывать локальные эпизоды: разговор на
собрании, конфликт с соседями, подозрительный взгляд сотрудника учреждения, потерю доверия
семьи, появление полезной связи, слухи во дворе, тревожный вызов в контору или чувство
морального компромисса. Но модель не должна превращать частное решение игрока в событие
государственного масштаба.

Игрок может быть идейным коммунистом, прагматиком или скрытым противником советской власти.
Для идейного коммуниста каждый год должен проверять верность идее, готовность жертвовать
личным ради общего дела и способность оправдывать жёсткость власти. Для прагматика каждый
год должен быть ситуацией риска и выгоды: он ищет ресурсы, связи, защиту и возможность
пережить перемены. Для скрытого противника власти каждый год должен ощущаться как опасная
игра: любое действие может приблизить цель, но также может вызвать подозрение, донос,
потерю безопасности или разрыв с близкими.

Важное правило: числовые метрики скрыты от игрока. Если выбор увеличивает подозрение,
LLM не должна писать “suspicion +2”. Вместо этого нужно показать сюжетное последствие:
за игроком стали внимательнее наблюдать, его имя появилось в неприятных разговорах, сосед
стал избегать прямого взгляда, знакомый посоветовал быть осторожнее. Если падает поддержка
людей, нужно описать холод в семье, отчуждение соседей, слухи или моральное осуждение.
Если растёт богатство, нужно показать появление ресурсов, еды, вещей, возможности влиять
на людей или покупать безопасность. Если растёт влияние, можно описывать должность,
знакомство, доступ к документам, уважение на собрании или способность решать чужие проблемы.
Если падает выживаемость, нужно показать усиление опасности: бессонные ночи, риск ареста,
тяжёлые условия, одиночество или потерю защиты. Если растёт лояльность, власть должна
воспринимать игрока надёжнее; если она падает, игрок становится человеком, которому не
доверяют.

Исторические факты года нельзя отменять. Игрок не может одним выбором прекратить гражданскую
войну, отменить НЭП, предотвратить образование СССР, изменить смерть Ленина, остановить
борьбу за власть, убрать Сталина, отменить курс на индустриализацию или сделать страну
капиталистической. Он не руководит всей страной, а находится внутри эпохи как человек,
которому приходится выживать, приспосабливаться, верить, предавать, помогать или
пользоваться чужой слабостью. Поэтому последствия выбора должны быть личными и локальными:
репутация, безопасность, семья, работа, деньги, связи, доверие, страх, слухи и отношение
власти."""


def _load_year_data() -> list[dict[str, Any]]:
    with HISTORY_DATA_PATH.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if not isinstance(data, list):
        raise RuntimeError("history_data.json must contain a list of year items")

    return data


YEAR_DATA: list[dict[str, Any]] = _load_year_data()


def _count_words(text: str) -> int:
    return len(WORD_RE.findall(text))


def _format_sources(item: dict[str, Any]) -> str:
    lines = []

    for source in item.get("sources", []):
        source_id = source.get("id", "source")
        title = source.get("title", "Источник")
        note = source.get("note") or source.get("url") or "без описания"
        lines.append(f"- {source_id}: {title}. {note}")

    return "\n".join(lines)


def _format_fact_sources(item: dict[str, Any]) -> str:
    lines = []

    for fact in item.get("real_fact_sources", []):
        text = fact.get("text", "")
        source_ids = ", ".join(fact.get("source_ids", []))
        lines.append(f"- {text} [source_ids: {source_ids}]")

    if lines:
        return "\n".join(lines)

    return "\n".join(f"- {fact}" for fact in item.get("real_facts", []))


def _build_context(item: dict[str, Any]) -> str:
    real_facts = _format_fact_sources(item)
    player_limits = "\n".join(f"- {fact}" for fact in item.get("player_limits", []))
    sources = _format_sources(item)

    role_lens = """
    Ракурс для трёх ролей:
    - Идейный коммунист должен воспринимать события через вопрос верности идее, партии и будущему.
    - Прагматик должен видеть в событиях риск, выгоду, возможность укрепиться или потерять защиту.
    - Скрытый противник власти должен искать слабости системы, но постоянно рисковать разоблачением.
    """.strip()

    text = f"""
    {item["year"]} — {item["title"]}

    Исторический фокус года:
    {item["historical_focus"].strip()}

    Реальные исторические факты года с source-id:
    {real_facts}

    Ограничения игрока:
    {player_limits}

    Источники:
    {sources}

    {role_lens}

    {COMMON_LLM_CONTEXT_BLOCK}
    """.strip()

    return text


def _build_turn(item: dict[str, Any]) -> HistoryTurn:
    real_facts = list(item.get("real_facts", []))
    player_limits = list(item.get("player_limits", []))
    sources = list(item.get("sources", []))
    fact_sources = list(item.get("real_fact_sources", []))

    return HistoryTurn(
        turn=int(item["turn"]),
        year=int(item["year"]),
        title=str(item["title"]),
        context=_build_context(item),
        immutable_facts=[*real_facts, *player_limits],
        question=str(item["question"]),
        choices=[
            ChoiceDefinition(
                id=str(choice["id"]),
                text=str(choice["text"]),
                effects=dict(choice["effects"]),
                tags=list(choice.get("tags", [])),
            )
            for choice in item["choices"]
        ],
        real_facts=real_facts,
        player_limits=player_limits,
        sources=sources,
        fact_sources=fact_sources,
    )


HISTORY_TURNS: list[HistoryTurn] = [_build_turn(item) for item in YEAR_DATA]


def _validate_contexts() -> None:
    for item in YEAR_DATA:
        year = int(item["year"])
        word_count = _count_words(str(item["historical_focus"]))

        if word_count < MIN_YEAR_CONTEXT_WORDS:
            raise RuntimeError(
                f"Unique historical focus for {year} is too short: "
                f"{word_count} words. Minimum required: {MIN_YEAR_CONTEXT_WORDS}."
            )

        if "Дополнительный исторический слой года:" in str(item["historical_focus"]):
            raise RuntimeError(f"{year}: old repeated historical_focus template is still present")

        source_ids = {
            source.get("id")
            for source in item.get("sources", [])
            if isinstance(source, dict) and source.get("id")
        }

        if not source_ids:
            raise RuntimeError(f"Sources for {year} are not configured")

        fact_sources = item.get("real_fact_sources", [])
        if not fact_sources:
            raise RuntimeError(f"{year}: real_fact_sources are not configured")

        for fact in fact_sources:
            ids = set(fact.get("source_ids", []))
            if not ids:
                raise RuntimeError(f"{year}: fact has no source_ids")
            if not ids.issubset(source_ids):
                raise RuntimeError(f"{year}: fact source_ids are not present in sources")

        for choice in item.get("choices", []):
            if not choice.get("tags"):
                raise RuntimeError(f"Choice {year}{choice.get('id')} has no tags")


_validate_contexts()


def get_history_turn(turn_number: int) -> HistoryTurn | None:
    for item in HISTORY_TURNS:
        if item.turn == turn_number:
            return item
    return None


def get_total_turns() -> int:
    return len(HISTORY_TURNS)


def get_context_word_counts() -> dict[int, int]:
    return {
        int(item["year"]): _count_words(str(item["historical_focus"]))
        for item in YEAR_DATA
    }


def get_full_context_word_counts() -> dict[int, int]:
    return {
        history_turn.year: _count_words(history_turn.context)
        for history_turn in HISTORY_TURNS
    }
