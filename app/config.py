import os
from dataclasses import dataclass
from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    telegram_bot_token: str
    ollama_enabled: bool
    ollama_model: str
    ollama_generate_url: str
    db_path: str


def _to_bool(value: str | None, default: bool) -> bool:
    if value is None:
        return default

    normalized = value.strip().lower()
    return normalized in {"1", "true", "yes", "y", "on"}


def load_settings() -> Settings:
    load_dotenv()

    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    if not token or token == "put_your_telegram_bot_token_here":
        raise RuntimeError(
            "TELEGRAM_BOT_TOKEN is not configured. "
            "Create .env from .env.example and put your Telegram bot token there."
        )

    return Settings(
        telegram_bot_token=token,
        ollama_enabled=_to_bool(os.getenv("OLLAMA_ENABLED"), default=True),
        ollama_model=os.getenv("OLLAMA_MODEL", "llama3.2:3b").strip(),
        ollama_generate_url=os.getenv(
            "OLLAMA_GENERATE_URL",
            "http://localhost:11434/api/generate",
        ).strip(),
        db_path=os.getenv("DB_PATH", "storage/games.db").strip(),
    )
