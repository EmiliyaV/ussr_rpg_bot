import logging

import aiohttp

from app.domain.models import ChoiceDefinition, HistoryTurn, RoleDefinition
from app.llm.prompts import build_final_prompt, build_year_result_prompt


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
        effect_meanings: list[str],
        state_description: str,
        memory: list[str],
    ) -> str:
        if not self._enabled:
            return ""

        prompt = build_year_result_prompt(
            history_turn=history_turn,
            role=role,
            choice=choice,
            effect_meanings=effect_meanings,
            state_description=state_description,
            memory=memory,
        )
        return await self._generate(prompt)

    async def generate_final(
        self,
        *,
        role: RoleDefinition,
        state_description: str,
        memory: list[str],
        ending_type: str,
    ) -> str:
        if not self._enabled:
            return ""

        prompt = build_final_prompt(
            role=role,
            state_description=state_description,
            memory=memory,
            ending_type=ending_type,
        )
        return await self._generate(prompt)

    async def _generate(self, prompt: str) -> str:
        payload = {
            "model": self._model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.55,
                "num_ctx": 8192,
                "num_predict": 400,
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
