# main.py
import asyncio
import logging
from aiogram import Bot
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram import Dispatcher
from aiogram.filters import Command
from config import TOKEN
from handlers import (
    start,
    set_username,
    add_task_handler,
    list_tasks_handler,
    navigate_tasks,
    delete_task_prompt,
    delete_task_by_description,
    process_description,
    process_day_and_time,
    help_handler
)
from scheduler import Scheduler
from storage import TaskStorage
from states import TaskStates
from globals import storage, scheduler, load_tasks_from_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    logger.info("🚀 Бот запускается...")

    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()

    scheduler.setup(bot, storage)
    scheduler.start()
    load_tasks_from_db()

    # Регистрация команд и состояний
    dp.message.register(start, Command("start"))
    dp.message.register(help_handler, Command("help"))
    dp.message.register(set_username, TaskStates.waiting_for_username)
    dp.message.register(process_day_and_time, TaskStates.waiting_for_day_and_time)
    dp.message.register(delete_task_by_description, TaskStates.waiting_for_task_description)
    dp.message.register(process_description, TaskStates.waiting_for_description)

    # Инлайн-кнопки
    dp.callback_query.register(add_task_handler, lambda c: c.data == "add_task")
    dp.callback_query.register(list_tasks_handler, lambda c: c.data == "list_tasks")
    dp.callback_query.register(navigate_tasks, lambda c: c.data.startswith("prev_") or c.data.startswith("next_"))
    dp.callback_query.register(delete_task_prompt, lambda c: c.data == "delete_task")
    dp.callback_query.register(help_handler, lambda c: c.data == "show_help")

    try:
        logger.info("🤖 Бот стартовал и готов к работе!")
        await dp.start_polling(bot)
    finally:
        logger.info("🛑 Бот остановлен")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())