from __future__ import annotations

import re
from dataclasses import dataclass


INTERNAL_TERMS = {
    "wealth",
    "loyalty",
    "influence",
    "suspicion",
    "survival",
    "people_support",
    "outcome_type",
    "severity",
    "tags",
    "major_events",
    "real_facts",
    "player_limits",
    "debug",
}

# Запрещаем не любые числа, а именно технические записи:
# +2, -1, + 3, - 4, 10/10, 7/10 и похожие оценочные/метрические формы.
TECHNICAL_NUMBER_PATTERNS = [
    re.compile(r"(?<!\w)[+-]\s*\d+(?!\w)"),
    re.compile(r"\b\d+\s*/\s*\d+\b"),
    re.compile(
        r"\b(?:wealth|loyalty|influence|suspicion|survival|people_support)\s*[:=]?\s*[+-]?\s*\d+\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b\d+\s*(?:wealth|loyalty|influence|suspicion|survival|people_support)\b",
        re.IGNORECASE,
    ),
]

# Здесь нельзя запрещать просто "пакт молотова": это нормальный исторический факт 1939 года.
# Запрещаем только формулировки, где игрок или текст отменяет/предотвращает крупную историю.
FORBIDDEN_HISTORY_REWRITE_PATTERNS = [
    re.compile(r"\bотменил\s+нэп\b"),
    re.compile(r"\bотменила\s+нэп\b"),
    re.compile(r"\bнэп\s+не\s+был\s+введен\b"),
    re.compile(r"\bнэп\s+не\s+был\s+введён\b"),

    re.compile(r"\bпредотвратил\s+образование\s+ссср\b"),
    re.compile(r"\bпредотвратила\s+образование\s+ссср\b"),
    re.compile(r"\bссср\s+не\s+был\s+создан\b"),

    re.compile(r"\bленин\s+не\s+умер\b"),
    re.compile(r"\bпредотвратил\s+смерть\s+ленина\b"),
    re.compile(r"\bпредотвратила\s+смерть\s+ленина\b"),

    re.compile(r"\bкиров\s+остался\s+жив\b"),
    re.compile(r"\bпредотвратил\s+убийство\s+кирова\b"),
    re.compile(r"\bпредотвратила\s+убийство\s+кирова\b"),

    re.compile(r"\bостановил\s+коллективизацию\b"),
    re.compile(r"\bостановила\s+коллективизацию\b"),
    re.compile(r"\bотменил\s+коллективизацию\b"),
    re.compile(r"\bотменила\s+коллективизацию\b"),

    re.compile(r"\bостановил\s+большой\s+террор\b"),
    re.compile(r"\bостановила\s+большой\s+террор\b"),
    re.compile(r"\bотменил\s+большой\s+террор\b"),
    re.compile(r"\bотменила\s+большой\s+террор\b"),

    re.compile(r"\bсверг\s+сталина\b"),
    re.compile(r"\bсталина\s+свергли\b"),
    re.compile(r"\bсталин\s+был\s+свергнут\b"),

    re.compile(r"\bпакт\s+молотова\s*[-—–]\s*риббентропа\s+не\s+был\s+заключен\b"),
    re.compile(r"\bпакт\s+молотова\s*[-—–]\s*риббентропа\s+не\s+был\s+заключён\b"),
    re.compile(r"\bпредотвратил\s+пакт\s+молотова\b"),
    re.compile(r"\bпредотвратила\s+пакт\s+молотова\b"),
    re.compile(r"\bотменил\s+пакт\s+молотова\b"),
    re.compile(r"\bотменила\s+пакт\s+молотова\b"),

    re.compile(r"\bпредотвратил\s+вторую\s+мировую\b"),
    re.compile(r"\bпредотвратила\s+вторую\s+мировую\b"),
    re.compile(r"\bвторая\s+мировая\s+война\s+не\s+началась\b"),
    re.compile(r"\bвойна\s+не\s+началась\b"),
]


@dataclass(frozen=True)
class ValidationResult:
    is_valid: bool
    reason: str = ""


def _normalize(text: str) -> str:
    return (
        text.lower()
        .replace("ё", "е")
        .replace("—", "-")
        .replace("–", "-")
    )


def _contains_internal_term(text: str) -> str | None:
    for term in INTERNAL_TERMS:
        pattern = re.compile(rf"(?<![A-Za-z0-9_]){re.escape(term)}(?![A-Za-z0-9_])", re.IGNORECASE)
        if pattern.search(text):
            return term

    return None


def _contains_technical_number(text: str) -> str | None:
    for pattern in TECHNICAL_NUMBER_PATTERNS:
        match = pattern.search(text)
        if match:
            return match.group(0)

    return None


def _contains_major_history_rewrite(normalized_text: str) -> str | None:
    for pattern in FORBIDDEN_HISTORY_REWRITE_PATTERNS:
        match = pattern.search(normalized_text)
        if match:
            return match.group(0)

    return None


def validate_llm_response(text: str) -> ValidationResult:
    prepared = text.strip()

    if not prepared:
        return ValidationResult(False, "empty response")

    internal_term = _contains_internal_term(prepared)
    if internal_term is not None:
        return ValidationResult(False, f"internal term leaked: {internal_term}")

    technical_number = _contains_technical_number(prepared)
    if technical_number is not None:
        return ValidationResult(False, f"technical number leaked: {technical_number}")

    rewrite = _contains_major_history_rewrite(_normalize(prepared))
    if rewrite is not None:
        return ValidationResult(False, f"major history rewrite detected: {rewrite}")

    return ValidationResult(True)
