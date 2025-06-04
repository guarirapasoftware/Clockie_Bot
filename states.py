# states.py
from aiogram.fsm.state import StatesGroup, State


class TaskStates(StatesGroup):
    waiting_for_username = State()
    waiting_for_description = State()
    waiting_for_day_and_time = State()
    waiting_for_task_description = State()