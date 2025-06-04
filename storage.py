# storage.py
import sqlite3
import os


class TaskStorage:
    def __init__(self):
        self.db_path = "tasks.db"
        self._initialize_db()

    def _initialize_db(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    task_id TEXT PRIMARY KEY,
                    chat_id INTEGER,
                    description TEXT,
                    time TEXT
                )
            """)
            conn.commit()

    def save_user(self, user_id, username):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO users (user_id, username)
                VALUES (?, ?)
            """, (user_id, username))
            conn.commit()

    def get_username(self, user_id):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT username FROM users WHERE user_id=?", (user_id,))
            row = cursor.fetchone()
            return row[0] if row else None

    def add_task(self, task_id, task_data):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO tasks (task_id, chat_id, description, time)
                VALUES (?, ?, ?, ?)
            """, (
                task_id,
                task_data["chat_id"],
                task_data["description"],
                task_data["time"].isoformat()
            ))
            conn.commit()

    def get_task(self, task_id):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM tasks WHERE task_id=?", (task_id,))
            row = cursor.fetchone()
            if row:
                return {"chat_id": row[1], "description": row[2], "time": row[3]}
            return None

    def remove_task(self, task_id):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM tasks WHERE task_id=?", (task_id,))
            conn.commit()

    def clear_all(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM tasks")
            conn.commit()

    def get_all_tasks(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT task_id, chat_id, description, time FROM tasks")
            rows = cursor.fetchall()
            return [
                {
                    "task_id": row[0],
                    "chat_id": row[1],
                    "description": row[2],
                    "time": row[3]
                } for row in rows
            ]