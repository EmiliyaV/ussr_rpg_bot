from __future__ import annotations

import logging

import aiohttp

from app.domain.models import ChoiceDefinition, HistoryTurn, RoleDefinition
from app.game.outcome_resolver import YearOutcome
from app.llm.prompts import build_final_prompt, build_year_result_prompt
from app.llm.response_validator import validate_llm_response


logger = logging.getLogger(__name__)


class OllamaClient:
    def __init__(
        self,
        *,
        enabled: bool,
        model: str,
        generate_url: str,
        timeout_seconds: int = 60,
    ) -> None:
        self._enabled = enabled
        self._model = model
        self._generate_url = generate_url
        self._timeout_seconds = timeout_seconds

    async def generate_year_result(
        self,
        *,
        history_turn: HistoryTurn,
        role: RoleDefinition,
        choice: ChoiceDefinition,
        outcome: YearOutcome,
        effect_meanings: list[str],
        state_description: str,
        memory: list[str],
        major_events: list[str],
    ) -> str:
        if not self._enabled:
            return ""

        prompt = build_year_result_prompt(
            history_turn=history_turn,
            role=role,
            choice=choice,
            outcome=outcome,
            effect_meanings=effect_meanings,
            state_description=state_description,
            memory=memory,
            major_events=major_events,
        )
        result = await self._generate(prompt)
        validation = validate_llm_response(result)
        if not validation.is_valid:
            logger.warning(
                "LLM year result rejected for %s: %s",
                history_turn.year,
                validation.reason,
            )
            return ""
        return result

    async def generate_final(
        self,
        *,
        role: RoleDefinition,
        state_description: str,
        memory: list[str],
        major_events: list[str],
        ending_type: str,
    ) -> str:
        if not self._enabled:
            return ""

        prompt = build_final_prompt(
            role=role,
            state_description=state_description,
            memory=memory,
            major_events=major_events,
            ending_type=ending_type,
        )
        result = await self._generate(prompt)
        validation = validate_llm_response(result)
        if not validation.is_valid:
            logger.warning(
                "LLM final result rejected for ending '%s': %s",
                ending_type,
                validation.reason,
            )
            return ""
        return result

    async def _generate(self, prompt: str) -> str:
        payload = {
            "model": self._model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.62,
                "num_ctx": 8192,
                "num_predict": 900,
            },
        }

        timeout = aiohttp.ClientTimeout(total=self._timeout_seconds)

        try:
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(self._generate_url, json=payload) as response:
                    if response.status >= 400:
                        text = await response.text()
                        logger.warning("Ollama error %s: %s", response.status, text)
                        return ""

                    data = await response.json()
                    return str(data.get("response", "")).strip()
        except Exception:
            logger.exception("Failed to call Ollama")
            return ""
