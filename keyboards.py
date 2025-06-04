# keyboards.py
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def main_menu_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Добавить задачу", callback_data="add_task")],
        [InlineKeyboardButton(text="📋 Список задач", callback_data="list_tasks")],
        [InlineKeyboardButton(text="❌ Удалить задачу", callback_data="delete_task")],
        [InlineKeyboardButton(text="❓ Справка", callback_data="show_help")]
    ])