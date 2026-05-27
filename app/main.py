import asyncio
import logging

from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from app.config import Settings, load_settings
from app.content.history import get_total_turns
from app.content.roles import ROLES
from app.game.engine import GameEngine
from app.game.rules import REQUIRED_TOTAL_TURNS
from app.llm.ollama_client import OllamaClient
from app.storage.repository import SqliteGameRepository
from app.ui.keyboards import choices_keyboard, next_turn_keyboard, restart_keyboard, roles_keyboard
from app.ui.messages import (
    build_debug_status_message,
    build_status_message,
    build_turn_message,
    help_message,
    intro_message,
    role_selected_message,
)


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)

router = Router()
engine: GameEngine | None = None
settings: Settings | None = None


def get_settings() -> Settings:
    if settings is None:
        raise RuntimeError("Settings are not initialized")

    return settings


def get_engine() -> GameEngine:
    if engine is None:
        raise RuntimeError("Game engine is not initialized")

    return engine


@router.message(Command("start"))
async def start(message: Message) -> None:
    await message.answer(
        intro_message(),
        reply_markup=roles_keyboard(),
    )


@router.message(Command("help"))
async def help_command(message: Message) -> None:
    await message.answer(help_message())


@router.message(Command("status"))
async def status_command(message: Message) -> None:
    game = get_engine().get_game(message.from_user.id)

    if game is None:
        await message.answer(
            "Активной игры нет. Напиши /start, чтобы начать.",
            reply_markup=roles_keyboard(),
        )
        return

    await message.answer(
        build_status_message(game),
        reply_markup=restart_keyboard(),
    )


@router.message(Command("debug_status"))
async def debug_status_command(message: Message) -> None:
    if not get_settings().debug_commands_enabled:
        await message.answer(
            "Отладочная команда отключена. "
            "Для локальной проверки установи DEBUG_COMMANDS_ENABLED=true в .env."
        )
        return

    game = get_engine().get_game(message.from_user.id)

    if game is None:
        await message.answer("Активной игры нет.")
        return

    await message.answer(build_debug_status_message(game))


@router.callback_query(F.data == "status")
async def status_callback(callback: CallbackQuery) -> None:
    game = get_engine().get_game(callback.from_user.id)

    if game is None:
        await callback.message.answer(
            "Активной игры нет. Напиши /start, чтобы начать.",
            reply_markup=roles_keyboard(),
        )
        await callback.answer()
        return

    await callback.message.answer(
        build_status_message(game),
        reply_markup=restart_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data == "restart")
async def restart_callback(callback: CallbackQuery) -> None:
    get_engine().restart_game(callback.from_user.id)

    await callback.message.answer(
        "Игра сброшена. Выбери новую роль:",
        reply_markup=roles_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data == "next_turn")
async def next_turn_callback(callback: CallbackQuery) -> None:
    game = get_engine().get_game(callback.from_user.id)

    if game is None:
        await callback.message.answer(
            "Активной игры нет. Напиши /start, чтобы начать.",
            reply_markup=roles_keyboard(),
        )
        await callback.answer()
        return

    if game.status != "active":
        await callback.message.answer(
            "Игра уже завершена.",
            reply_markup=restart_keyboard(),
        )
        await callback.answer()
        return

    current_turn = get_engine().get_current_turn(game)

    if current_turn is None:
        await callback.message.answer(
            "Следующий ход не найден. Игра остановлена.",
            reply_markup=restart_keyboard(),
        )
        await callback.answer()
        return

    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except Exception:
        logging.exception("Failed to remove next-turn keyboard")

    await callback.message.answer(
        build_turn_message(current_turn, game),
        reply_markup=choices_keyboard(current_turn),
    )

    await callback.answer()


@router.callback_query(F.data.startswith("role:"))
async def select_role(callback: CallbackQuery) -> None:
    role_id = callback.data.split(":", maxsplit=1)[1]

    if role_id not in ROLES:
        await callback.answer("Неизвестная роль.", show_alert=True)
        return

    state = get_engine().start_game(
        user_id=callback.from_user.id,
        role_id=role_id,
    )

    role = ROLES[role_id]
    current_turn = get_engine().get_current_turn(state)

    await callback.message.answer(role_selected_message(role))

    if current_turn is None:
        await callback.message.answer("Не удалось загрузить первый ход.")
        await callback.answer()
        return

    await callback.message.answer(
        build_turn_message(current_turn, state),
        reply_markup=choices_keyboard(current_turn),
    )

    await callback.answer()


@router.callback_query(F.data.startswith("choice:"))
async def choose_action(callback: CallbackQuery) -> None:
    data = callback.data or ""
    parts = data.split(":")

    game = get_engine().get_game(callback.from_user.id)
    if game is None:
        await callback.answer("Активной игры нет. Напиши /start, чтобы начать.", show_alert=True)
        return

    if len(parts) == 3:
        try:
            callback_turn = int(parts[1])
        except ValueError:
            await callback.answer("Некорректная кнопка выбора.", show_alert=True)
            return

        choice_id = parts[2].strip().upper()

        if game.turn != callback_turn:
            await callback.answer(
                "Это кнопка старого хода. Нажми актуальную кнопку в последнем сообщении.",
                show_alert=True,
            )
            return
    elif len(parts) == 2:
        choice_id = parts[1].strip().upper()
    else:
        await callback.answer("Некорректная кнопка выбора.", show_alert=True)
        return

    try:
        result = await get_engine().apply_choice(
            user_id=callback.from_user.id,
            choice_id=choice_id,
        )
    except Exception as exc:
        logging.exception("Failed to apply choice")
        await callback.answer(str(exc), show_alert=True)
        return

    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except Exception:
        logging.exception("Failed to remove inline keyboard")

    if result.final_text is not None:
        await callback.message.answer(result.year_result_text)
        await callback.message.answer(
            result.final_text,
            reply_markup=restart_keyboard(),
        )
        await callback.answer()
        return

    await callback.message.answer(
        result.year_result_text,
        reply_markup=next_turn_keyboard(),
    )

    await callback.answer()

async def main() -> None:
    global engine, settings

    settings = load_settings()

    total_turns = get_total_turns()

    if total_turns < REQUIRED_TOTAL_TURNS:
        raise RuntimeError(
            f"В истории сейчас {total_turns} ходов, нужно {REQUIRED_TOTAL_TURNS}. "
            "Добавь все годы 1920–1939."
        )

    repository = SqliteGameRepository(settings.db_path)
    llm_client = OllamaClient(
        enabled=settings.ollama_enabled,
        model=settings.ollama_model,
        generate_url=settings.ollama_generate_url,
    )

    engine = GameEngine(
        repository=repository,
        llm_client=llm_client,
    )

    bot = Bot(token=settings.telegram_bot_token)
    dispatcher = Dispatcher()
    dispatcher.include_router(router)

    logging.info("Bot started")
    await dispatcher.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
