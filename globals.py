# globals.py
from storage import TaskStorage
from scheduler import Scheduler
import logging
from datetime import datetime
from config import TIMEZONE

logger = logging.getLogger(__name__)
storage = TaskStorage()
scheduler = Scheduler()


def load_tasks_from_db():
    """Загружает все задачи из БД в планировщик"""
    tasks = storage.get_all_tasks()
    for task in tasks:
        try:
            task_time = datetime.fromisoformat(task["time"])
            scheduler.add_reminder(task["task_id"], task_time)
            logger.info(f"🔄 Восстановлена задача: {task['task_id']} на {task_time}")
        except Exception as e:
            logger.error(f"🔄 Не удалось восстановить задачу: {e}")