# scheduler.py
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from config import TIMEZONE
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class Scheduler:
    def __init__(self):
        self.scheduler = AsyncIOScheduler(timezone=TIMEZONE)
        self.bot = None
        self.storage = None

    def setup(self, bot, storage):
        self.bot = bot
        self.storage = storage

    def add_reminder(self, task_id, run_date):
        logger.info(f"Добавление напоминания: {task_id} на {run_date}")
        if self.scheduler.get_job(task_id):
            self.scheduler.remove_job(task_id)

        self.scheduler.add_job(
            self.send_reminder,
            "date",
            run_date=run_date,
            args=[task_id],
            id=task_id
        )

    async def send_reminder(self, task_id: str):
        logger.info(f"🔔 Отправка напоминания: {task_id}")
        task = self.storage.get_task(task_id)

        if not task:
            logger.warning(f"Задача {task_id} не найдена")
            return

        if not self.bot:
            logger.error("Бот не инициализирован")
            return

        try:
            await self.bot.send_message(
                chat_id=task["chat_id"],
                text=f"🔔 Напоминание!\n{task['description']}"
            )
        except Exception as e:
            logger.error(f"Ошибка отправки: {e}")
        finally:
            self.storage.remove_task(task_id)


    def start(self):
        try:
            self.scheduler.start()
            logger.info("Планировщик успешно запущен")
        except Exception as e:
            logger.error(f"Ошибка запуска планировщика: {e}")

    def shutdown(self):
        self.scheduler.shutdown()
        logger.info("Планировщик остановлен")