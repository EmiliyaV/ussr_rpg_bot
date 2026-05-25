from pathlib import Path
import textwrap


ROOT = Path.cwd()


def write_file(relative_path: str, content: str) -> None:
    path = ROOT / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(content).lstrip(), encoding="utf-8")
    print(f"[OK] {relative_path}")


def require_project() -> None:
    required = [
        "app/main.py",
        "app/ui/keyboards.py",
        "app/ui/messages.py",
        "app/game/engine.py",
        "app/content/history.py",
    ]

    missing = [item for item in required if not (ROOT / item).exists()]
    if missing:
        raise RuntimeError(
            "Скрипт нужно запускать из корня проекта.\n"
            "Не найдены файлы:\n"
            + "\n".join(f"- {item}" for item in missing)
        )


def main() -> None:
    require_project()

    write_file("app/ui/keyboards.py", """
    from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

    from app.content.roles import ROLES
    from app.domain.models import HistoryTurn


    def roles_keyboard() -> InlineKeyboardMarkup:
        rows = []

        for role_id, role in ROLES.items():
            rows.append(
                [
                    InlineKeyboardButton(
                        text=role.name,
                        callback_data=f"role:{role_id}",
                    )
                ]
            )

        return InlineKeyboardMarkup(inline_keyboard=rows)


    def choices_keyboard(history_turn: HistoryTurn) -> InlineKeyboardMarkup:
        choice_buttons = [
            InlineKeyboardButton(
                text=choice.id,
                callback_data=f"choice:{choice.id}",
            )
            for choice in history_turn.choices
        ]

        return InlineKeyboardMarkup(
            inline_keyboard=[
                choice_buttons,
                [
                    InlineKeyboardButton(
                        text="📊 Положение",
                        callback_data="status",
                    )
                ],
            ]
        )


    def next_turn_keyboard() -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="➡️ Далее",
                        callback_data="next_turn",
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="📊 Положение",
                        callback_data="status",
                    )
                ],
            ]
        )


    def restart_keyboard() -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🔁 Начать заново",
                        callback_data="restart",
                    )
                ]
            ]
        )
    """)

    write_file("app/ui/messages.py", """
    import re
    import textwrap

    from app.content.roles import ROLES
    from app.domain.models import GameState, HistoryTurn, RoleDefinition
    from app.game.stat_interpreter import describe_state_for_player


    def _normalize_text(text: str) -> str:
        prepared = textwrap.dedent(text).replace("\\t", " ")
        raw_lines = prepared.splitlines()

        paragraphs: list[str] = []
        current: list[str] = []

        for raw_line in raw_lines:
            line = re.sub(r"\\s+", " ", raw_line.strip())

            if not line:
                if current:
                    paragraphs.append(" ".join(current))
                    current = []
                continue

            current.append(line)

        if current:
            paragraphs.append(" ".join(current))

        return "\\n\\n".join(paragraphs).strip()


    def _shorten(text: str, limit: int) -> str:
        normalized = _normalize_text(text)

        if len(normalized) <= limit:
            return normalized

        cut = normalized[:limit].rstrip()
        last_dot = max(cut.rfind("."), cut.rfind("!"), cut.rfind("?"))

        if last_dot > limit * 0.55:
            return cut[: last_dot + 1]

        return cut + "..."


    def _extract_short_context(context: str, limit: int = 900) -> str:
        cleaned = _normalize_text(context)

        marker = "Исторический фокус года:"
        if marker in cleaned:
            after_marker = cleaned.split(marker, maxsplit=1)[1].strip()
            stop_markers = [
                "Неизменяемые факты:",
                "Ракурс для трёх ролей:",
                "Разрешённые типы локальных последствий:",
                "Игровая рамка этого проекта",
            ]

            for stop_marker in stop_markers:
                if stop_marker in after_marker:
                    after_marker = after_marker.split(stop_marker, maxsplit=1)[0].strip()

            return _shorten(after_marker, limit)

        return _shorten(cleaned, limit)


    def _format_immutable_facts(history_turn: HistoryTurn) -> str:
        return "\\n".join(f"— {_normalize_text(fact)}" for fact in history_turn.immutable_facts)


    def _format_choices(history_turn: HistoryTurn) -> str:
        lines = []

        for choice in history_turn.choices:
            lines.append(f"{choice.id}. {_normalize_text(choice.text)}")

        return "\\n".join(lines)


    def intro_message() -> str:
        return (
            "СССР: 20 вопросов\\n\\n"
            "Историческая ролевая игра в Telegram.\\n"
            "Ты выбираешь роль и проходишь 20 ходов: с 1920 по 1939 год. "
            "К 1940 году игра подводит итог твоей личной судьбы.\\n\\n"
            "Выбери роль:"
        )


    def help_message() -> str:
        return (
            "Команды:\\n"
            "/start — начать новую игру\\n"
            "/status — показать текущее положение без чисел\\n"
            "/debug_status — показать скрытые числа для отладки\\n"
            "/help — справка\\n\\n"
            "Правила:\\n"
            "- крупные события СССР нельзя отменить одним выбором;\\n"
            "- выбор влияет на личную судьбу персонажа;\\n"
            "- внутренние метрики считает код;\\n"
            "- Ollama используется только для атмосферного текста последствий;\\n"
            "- после итога года нужно нажать «Далее», чтобы перейти к следующему ходу."
        )


    def role_selected_message(role: RoleDefinition) -> str:
        return (
            f"Роль выбрана: {role.name}\\n\\n"
            f"{_normalize_text(role.description)}\\n\\n"
            "Игра начинается."
        )


    def build_turn_message(history_turn: HistoryTurn, state: GameState) -> str:
        role = ROLES[state.role_id]
        short_context = _extract_short_context(history_turn.context)
        immutable = _format_immutable_facts(history_turn)
        choices = _format_choices(history_turn)

        return (
            f"Ход {history_turn.turn}/20. {history_turn.year} год\\n"
            f"{_normalize_text(history_turn.title)}\\n\\n"
            f"Роль: {role.name}\\n\\n"
            f"Краткий контекст:\\n"
            f"{short_context}\\n\\n"
            f"Что нельзя изменить:\\n"
            f"{immutable}\\n\\n"
            f"Вопрос:\\n"
            f"{_normalize_text(history_turn.question)}\\n\\n"
            f"Варианты:\\n"
            f"{choices}\\n\\n"
            "Нажми A, B или C ниже."
        )


    def build_status_message(state: GameState) -> str:
        return describe_state_for_player(state)


    def build_debug_status_message(state: GameState) -> str:
        role = ROLES[state.role_id]
        lines = [f"{key}: {value}" for key, value in state.stats.items()]

        return (
            "DEBUG STATUS\\n\\n"
            f"Роль: {role.name}\\n"
            f"Ход: {state.turn}\\n"
            f"Статус: {state.status}\\n"
            f"ending_type: {state.ending_type}\\n\\n"
            "Скрытые показатели:\\n"
            + "\\n".join(lines)
        )
    """)

    write_file("app/main.py", """
    import asyncio
    import logging

    from aiogram import Bot, Dispatcher, F, Router
    from aiogram.filters import Command
    from aiogram.types import CallbackQuery, Message

    from app.config import load_settings
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
        choice_id = callback.data.split(":", maxsplit=1)[1]

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
        global engine

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
    """)

    write_file("scripts/check_ui_flow.py", """
    from pathlib import Path
    import inspect
    import sys

    PROJECT_ROOT = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(PROJECT_ROOT))

    from app.ui import keyboards, messages
    import app.main as main_module


    def check(condition: bool, message: str) -> None:
        if not condition:
            raise SystemExit("[FAIL] " + message)

        print("[OK] " + message)


    def main() -> None:
        keyboard_source = inspect.getsource(keyboards)
        message_source = inspect.getsource(messages)
        main_source = inspect.getsource(main_module)

        check("next_turn_keyboard" in keyboard_source, "есть клавиатура Далее")
        check('callback_data="next_turn"' in keyboard_source, "кнопка Далее имеет callback next_turn")
        check("choice.id" in keyboard_source, "кнопки выбора используют короткие A/B/C")
        check("choice.text" not in keyboard_source, "полный текст выбора не выводится на кнопках")

        check("_normalize_text" in message_source, "есть нормализация текста")
        check("_extract_short_context" in message_source, "есть извлечение короткого контекста")
        check("_format_choices" in message_source, "полные варианты выводятся в сообщении")
        check("Нажми A, B или C ниже" in message_source, "сообщение объясняет короткие кнопки")

        check("next_turn_callback" in main_source, "есть обработчик Далее")
        check("next_turn_keyboard()" in main_source, "после выбора показывается кнопка Далее")
        check("build_turn_message(current_turn, game)" in main_source, "следующий ход показывается только после Далее")

        print()
        print("UI flow checks passed.")


    if __name__ == "__main__":
        main()
    """)

    print()
    print("[DONE] UI-flow исправлен.")
    print()
    print("Проверь:")
    print("python scripts/check_ui_flow.py")
    print("python scripts/check_project_steps.py")
    print()
    print("Запуск:")
    print("python -m app.main")


if __name__ == "__main__":
    main()