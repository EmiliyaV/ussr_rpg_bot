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
            callback_data=f"choice:{history_turn.turn}:{choice.id}",
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
