import os
from dotenv import load_dotenv
from note import Note
import pymysql
from pymysql.cursors import DictCursor

# Завантажуємо змінні з файлу .env
load_dotenv()

# Зчитуємо параметри
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")

# Перевіряємо, чи всі критичні змінні задані у .env
if not all([DB_USER, DB_PASSWORD, DB_NAME]):
    raise ValueError(
        "❌ Помилка: Не заповнено обов'язкові змінні середовища (DB_USER, DB_PASSWORD або DB_NAME) у файлі .env!"
    )

DB_CONFIG = {
    "host": DB_HOST,
    "user": DB_USER,
    "password": DB_PASSWORD,
    "database": DB_NAME,
    "charset": "utf8mb4",
    "cursorclass": DictCursor,
}


class NoteRepository:

    def __init__(self):
        self._create_table()

    def _get_connection(self):
        return pymysql.connect(**DB_CONFIG)

    def _create_table(self):
        """Створює таблицю notes, якщо вона ще не існує"""
        connection = self._get_connection()
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS notes (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        title VARCHAR(255) NOT NULL,
                        content TEXT NOT NULL,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """
                )
            connection.commit()
        finally:
            connection.close()

    def add(self, title: str, content: str) -> Note:
        connection = self._get_connection()
        try:
            with connection.cursor() as cursor:
                query = "INSERT INTO notes (title, content) VALUES (%s, %s)"
                cursor.execute(query, (title, content))
                connection.commit()
                note_id = cursor.lastrowid
            return self.get_by_id(note_id)
        finally:
            connection.close()

    def get_all(self) -> list[Note]:
        connection = self._get_connection()
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT * FROM notes")
                rows = cursor.fetchall()
                return [
                    Note(
                        note_id=row["id"],
                        title=row["title"],
                        content=row["content"],
                        created_at=row["created_at"],
                    )
                    for row in rows
                ]
        finally:
            connection.close()

    def get_by_id(self, note_id: int) -> Note | None:
        connection = self._get_connection()
        try:
            with connection.cursor() as cursor:
                query = "SELECT * FROM notes WHERE id = %s"
                cursor.execute(query, (note_id,))
                row = cursor.fetchone()
                if row:
                    return Note(
                        note_id=row["id"],
                        title=row["title"],
                        content=row["content"],
                        created_at=row["created_at"],
                    )
                return None
        finally:
            connection.close()

    def update(self, note_id: int, title: str, content: str) -> Note | None:
        connection = self._get_connection()
        try:
            with connection.cursor() as cursor:
                query = (
                    "UPDATE notes SET title = %s, content = %s WHERE id = %s"
                )
                cursor.execute(query, (title, content, note_id))
                connection.commit()

                if cursor.rowcount > 0:
                    return self.get_by_id(note_id)
                return None
        finally:
            connection.close()

    def delete(self, note_id: int) -> bool:
        connection = self._get_connection()
        try:
            with connection.cursor() as cursor:
                query = "DELETE FROM notes WHERE id = %s"
                cursor.execute(query, (note_id,))
                connection.commit()
                return cursor.rowcount > 0
        finally:
            connection.close()
