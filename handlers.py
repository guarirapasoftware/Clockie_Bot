# handlers.py
from aiogram import types
from aiogram.fsm.context import FSMContext
from datetime import datetime, timedelta
import logging
from config import TIMEZONE
from states import TaskStates
from globals import storage, scheduler
from keyboards import main_menu_keyboard
from utils import get_paginated_tasks, get_pagination_keyboard

logger = logging.getLogger(__name__)

DAYS_MAP = {
    'пн': 'понедельник',
    'вт': 'вторник',
    'ср': 'среда',
    'чт': 'четверг',
    'пт': 'пятница',
    'сб': 'суббота',
    'вс': 'воскресенье'
}

RU_MONTHS = {
    1: "января", 2: "февраля", 3: "марта",
    4: "апреля", 5: "мая", 6: "июня",
    7: "июля", 8: "августа", 9: "сентября",
    10: "октября", 11: "ноября", 12: "декабря"
}

RU_DAYS = {
    0: "понедельник",
    1: "вторник",
    2: "среда",
    3: "четверг",
    4: "пятница",
    5: "суббота",
    6: "воскресенье"
}


async def start(message: types.Message, state: FSMContext):
    await state.clear()
    logger.info("📩 Пользователь написал /start")

    user_id = message.from_user.id
    username = storage.get_username(user_id)

    if not username:
        await message.answer("Привет! Как я могу к тебе обращаться?")
        await state.set_state(TaskStates.waiting_for_username)
    else:
        await message.answer(f"👋 Привет, <b>{username}</b>!\n\nВыбери действие:", reply_markup=main_menu_keyboard())


async def set_username(message: types.Message, state: FSMContext):
    logger.info("📩 Получено имя пользователя")
    user_id = message.from_user.id
    username = message.text.strip()

    storage.save_user(user_id, username)
    await message.answer(f"✅ Приятно познакомиться, <b>{username}</b>!", reply_markup=main_menu_keyboard())
    await state.set_state(None)


async def add_task_handler(callback: types.CallbackQuery, state: FSMContext):
    logger.info("📩 Пользователь нажал '➕ Добавить задачу'")
    user_id = callback.from_user.id
    username = storage.get_username(user_id)

    if not username:
        await callback.message.answer("Сначала представься мне!")
        await state.set_state(TaskStates.waiting_for_username)
    else:
        await callback.message.answer("📝 Введи описание задачи:")
        await state.set_state(TaskStates.waiting_for_description)


async def process_description(message: types.Message, state: FSMContext):
    logger.info("📩 Получено описание задачи")

    if not message.text:
        await message.answer("❌ Описание не может быть пустым.")
        return

    logger.info("🧠 Переход в состояние waiting_for_day_and_time")
    await state.update_data(description=message.text)
    await message.answer("📅 Введи день (необязательно) и время:\nНапример: 14:30 или 10.06 18:00")
    await state.set_state(TaskStates.waiting_for_day_and_time)


async def process_day_and_time(message: types.Message, state: FSMContext):
    logger.info("📩 Получен день и время от пользователя")
    text = message.text.strip().lower()
    now = datetime.now(TIMEZONE)
    data = await state.get_data()
    description = data.get("description")
    user_id = message.from_user.id
    username = storage.get_username(user_id)

    try:
        parts = text.split()

        if len(parts) == 1:
            time_part = parts[0]
            day_part = None
        elif len(parts) == 2:
            day_part, time_part = parts
        else:
            raise ValueError("Формат: [ДД.ММ] ЧЧ:ММ")

        if ':' not in time_part:
            raise ValueError("Неверный формат времени")

        hours, minutes = map(int, time_part.split(':'))
        if not (0 <= hours <= 23 and 0 <= minutes <= 59):
            raise ValueError("Время вне диапазона")

        task_time = now.replace(hour=hours, minute=minutes, second=0, microsecond=0)

        if day_part:
            if '.' in day_part:
                day, month = map(int, day_part.split('.'))
                task_time = now.replace(day=day, month=month, hour=hours, minute=minutes, second=0, microsecond=0)
                if task_time <= now:
                    task_time = task_time.replace(year=now.year + 1)
            elif day_part[:2] in DAYS_MAP:
                day_key = day_part[:2]
                target_day_name = DAYS_MAP[day_key]
                target_weekday = list(DAYS_MAP.values()).index(target_day_name)

                days_ahead = (target_weekday - now.weekday() + 7) % 7
                if days_ahead == 0 and now.hour >= hours and now.minute >= minutes:
                    days_ahead += 7

                task_time = now.replace(hour=hours, minute=minutes, second=0, microsecond=0) + timedelta(days=days_ahead)

        elif task_time <= now:
            task_time += timedelta(days=1)

        task_id = f"{user_id}_{int(task_time.timestamp())}"

        storage.add_task(task_id, {
            "chat_id": message.chat.id,
            "description": description,
            "time": task_time
        })

        scheduler.add_reminder(task_id, task_time)

        ru_day_name = RU_DAYS.get(task_time.weekday(), "")
        ru_month_name = RU_MONTHS.get(task_time.month, "")
        formatted_date = f"{ru_day_name}, {task_time.day} {ru_month_name} {task_time.strftime('%H:%M')}"

        logger.info(f"✅ Задача добавлена: {description} на {formatted_date}")
        await message.answer(
            f"✅ Задача добавлена!\n"
            f"📝 Описание: {description}\n"
            f"⏰ Время: {formatted_date}",
            reply_markup=main_menu_keyboard()
        )

    except ValueError as ve:
        logger.warning(f"❌ Ошибка ввода дня/времени: {ve}")
        await message.answer("❌ Неверный формат!\nИспользуй:\n• 14:30 (на сегодня)\n• 10.06 18:00 (на конкретную дату)\n• Пн 15:00 (на день недели)")
    finally:
        await state.clear()


async def list_tasks_handler(callback: types.CallbackQuery, state: FSMContext):
    logger.info("📩 Пользователь нажал '📋 Список задач'")
    user_id = callback.from_user.id
    all_tasks = storage.get_all_tasks()
    tasks = [task for task in all_tasks if task["task_id"].startswith(f"{user_id}_")]

    if not tasks:
        await callback.message.answer("📭 У вас нет активных задач.", reply_markup=main_menu_keyboard())
        return

    await state.update_data(tasks=tasks, page=0)
    await send_task_page(callback, tasks, 0)


async def send_task_page(callback: types.CallbackQuery, tasks, page):
    from utils import get_paginated_tasks, get_pagination_keyboard

    paginated_tasks = get_paginated_tasks(tasks, page)
    total_pages = (len(tasks) + 4) // 5

    response = "<b>📄 Ваши задачи:</b>\n\n"
    for task in paginated_tasks:
        try:
            task_time = datetime.fromisoformat(task['time'])
            ru_day = RU_DAYS.get(task_time.weekday(), "")
            ru_month = RU_MONTHS.get(task_time.month, "")
            formatted_time = f"{ru_day}, {task_time.day} {ru_month} {task_time.strftime('%H:%M')}"
        except Exception:
            formatted_time = task['time']

        response += f"📌 <b>{task['description']}</b>\n"
        response += f"⏰ {formatted_time}\n\n"

    markup = get_pagination_keyboard(page, total_pages)
    await callback.message.answer(response, reply_markup=markup)


async def navigate_tasks(callback: types.CallbackQuery, state: FSMContext):
    data = callback.data
    action, current_page = data.split('_')
    current_page = int(current_page)

    user_data = await state.get_data()
    tasks = user_data.get("tasks", [])

    if not tasks:
        await callback.answer("⚠️ Сначала открой список задач")
        return

    total_pages = (len(tasks) + 4) // 5
    new_page = current_page

    if action == "prev":
        new_page = max(0, current_page - 1)
    elif action == "next":
        new_page = min(total_pages - 1, current_page + 1)

    await callback.message.delete()
    await send_task_page(callback, tasks, new_page)


async def delete_task_prompt(callback: types.CallbackQuery, state: FSMContext):
    logger.info("📩 Пользователь нажал '❌ Удалить задачу'")
    user_id = callback.from_user.id

    all_tasks = storage.get_all_tasks()
    tasks = [task for task in all_tasks if task["task_id"].startswith(f"{user_id}_")]

    if not tasks:
        await callback.answer("❌ У вас нет задач для удаления")
        return

    await callback.message.answer("🗑️ Введи название задачи, которую хочешь удалить:")
    await state.set_state(TaskStates.waiting_for_task_description)


async def delete_task_by_description(message: types.Message, state: FSMContext):
    logger.info("📩 Получено название задачи для удаления")
    description_to_delete = message.text.strip()
    user_id = message.from_user.id

    all_tasks = storage.get_all_tasks()
    tasks = [task for task in all_tasks if task["task_id"].startswith(f"{user_id}_")]
    found_tasks = [t for t in tasks if t["description"].lower() == description_to_delete.lower()]

    if not found_tasks:
        await message.answer("❌ Задача с таким названием не найдена.")
        await message.answer("Выберите действие:", reply_markup=main_menu_keyboard())
        await state.clear()
        return

    deleted_count = 0
    for task in found_tasks:
        task_id = task["task_id"]
        try:
            scheduler.scheduler.remove_job(task_id)
            storage.remove_task(task_id)
            deleted_count += 1
        except Exception as e:
            logger.error(f"Ошибка при удалении задачи {task_id}: {e}")

    if deleted_count > 0:
        await message.answer(f"✅ Удалено {deleted_count} задач(и): «{description_to_delete}»", reply_markup=main_menu_keyboard())
    else:
        await message.answer("❌ Не удалось удалить задачи.", reply_markup=main_menu_keyboard())

    await state.clear()


async def help_handler(callback: types.CallbackQuery | types.Message):
    logger.info("📩 Пользователь нажал '❓ Справка'")
    text = (
        "<b>📚 Справка по боту</b>\n\n"
        "📌 <b>Как добавить задачу:</b>\n"
        "1. Нажми '➕ Добавить задачу'\n"
        "2. Введи описание\n"
        "3. Укажи время в одном из форматов:\n"
        "   • Только время → <code>14:30</code> (на сегодня)\n"
        "   • Дата + время → <code>10.06 18:00</code> (на конкретный день)\n"
        "   • День недели + время → <code>Пн 15:00</code> (ближайший понедельник)\n\n"

        "📌 <b>Как посмотреть задачи:</b>\n"
        "Нажми '📋 Список задач' — увидишь их постранично.\n"
        "Кнопки '⬅️ Назад' и '➡️ Вперёд' помогут листать.\n\n"

        "📌 <b>Как удалить задачу:</b>\n"
        "Нажми '❌ Удалить задачу' → введи точное название задачи.\n\n"

        "📌 <b>Примеры ввода:</b>\n"
        "• <code>14:30</code> → Сегодня в 14:30\n"
        "• <code>10.06 18:00</code> → 10 июня в 18:00\n"
        "• <code>Пт 9:00</code> → Ближайшая пятница в 9:00"
    )

    if isinstance(callback, types.CallbackQuery):
        await callback.message.answer(text, reply_markup=main_menu_keyboard())
    else:
        await callback.answer(text, reply_markup=main_menu_keyboard())