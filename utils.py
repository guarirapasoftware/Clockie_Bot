# utils.py
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

TASKS_PER_PAGE = 5


def get_paginated_tasks(tasks, page):
    start = page * TASKS_PER_PAGE
    end = start + TASKS_PER_PAGE
    return tasks[start:end]


def get_pagination_keyboard(current_page, total_pages):
    buttons = []
    if current_page > 0:
        buttons.append(InlineKeyboardButton(text="⬅️ Назад", callback_data=f"prev_{current_page}"))
    if current_page < total_pages - 1:
        buttons.append(InlineKeyboardButton(text="➡️ Вперёд", callback_data=f"next_{current_page}"))

    return InlineKeyboardMarkup(inline_keyboard=[buttons])