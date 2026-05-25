from pathlib import Path
import sys
import asyncio

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from app.config import load_settings
from app.llm.ollama_client import OllamaClient


async def main() -> None:
    settings = load_settings()
    client = OllamaClient(
        enabled=True,
        model=settings.ollama_model,
        generate_url=settings.ollama_generate_url,
        timeout_seconds=30,
    )

    result = await client._generate(
        "Ответь одним коротким предложением по-русски: Ollama работает."
    )

    if not result:
        raise SystemExit("Ollama did not return a response.")

    print(result)


if __name__ == "__main__":
    asyncio.run(main())
