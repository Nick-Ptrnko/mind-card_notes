import os
from datetime import datetime
from zoneinfo import ZoneInfo

import pymysql
from dotenv import load_dotenv
from pymysql.cursors import DictCursor
from pymysql.err import IntegrityError

from note import Note

# Завантажуємо змінні з файлу .env
load_dotenv()

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")

# Часовий пояс, у якому зберігається й показується час створення нотаток
APP_TIMEZONE = os.getenv("APP_TIMEZONE", "Europe/Kyiv")
APP_TZ = ZoneInfo(APP_TIMEZONE)

# Перевірка наявності критичних параметрів (захист від захардкоджених секретів)
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

DUPLICATE_ENTRY_ERROR = 1062


class DuplicateTitleError(Exception):
    """Нотатка з такою назвою вже існує."""


def _is_duplicate(error: IntegrityError) -> bool:
    return bool(error.args) and error.args[0] == DUPLICATE_ENTRY_ERROR


def now_local() -> datetime:
    """Поточний час у часовому поясі застосунку (без tzinfo, для колонки DATETIME)."""
    return datetime.now(APP_TZ).replace(tzinfo=None)


class NoteRepository:

    def __init__(self):
        self._create_table()

    def _get_connection(self):
        return pymysql.connect(**DB_CONFIG)

    def _create_table(self):
        """Створює таблицю notes (якщо її ще немає) і гарантує UNIQUE на title"""
        connection = self._get_connection()
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS notes (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        title VARCHAR(255) NOT NULL,
                        content TEXT NOT NULL,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE KEY uq_notes_title (title)
                    )
                """
                )
                self._ensure_unique_title(cursor)
            connection.commit()
        finally:
            connection.close()

    def _ensure_unique_title(self, cursor) -> None:
        """Міграція: додає UNIQUE на title, якщо таблиця була створена раніше без нього."""
        cursor.execute(
            """
            SELECT COUNT(*) AS cnt
            FROM information_schema.statistics
            WHERE table_schema = DATABASE()
              AND table_name = 'notes'
              AND column_name = 'title'
              AND non_unique = 0
            """
        )
        if cursor.fetchone()["cnt"] > 0:
            return
        try:
            cursor.execute(
                "ALTER TABLE notes ADD UNIQUE KEY uq_notes_title (title)"
            )
        except IntegrityError as error:
            if _is_duplicate(error):
                raise RuntimeError(
                    "Не вдалося додати UNIQUE на notes.title: у базі вже є нотатки "
                    "з однаковими назвами. Знайдіть їх запитом "
                    "SELECT title, COUNT(*) FROM notes GROUP BY title "
                    "HAVING COUNT(*) > 1; перейменуйте дублікати й запустіть знову."
                ) from error
            raise

    def add(self, title: str, content: str) -> Note:
        connection = self._get_connection()
        try:
            with connection.cursor() as cursor:
                query = (
                    "INSERT INTO notes (title, content, created_at) "
                    "VALUES (%s, %s, %s)"
                )
                cursor.execute(query, (title, content, now_local()))
                connection.commit()
                note_id = cursor.lastrowid
        except IntegrityError as error:
            if _is_duplicate(error):
                raise DuplicateTitleError(title) from error
            raise
        finally:
            connection.close()
        return self.get_by_id(note_id)

    def get_all(self) -> list[Note]:
        connection = self._get_connection()
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT * FROM notes ORDER BY id")
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
        except IntegrityError as error:
            if _is_duplicate(error):
                raise DuplicateTitleError(title) from error
            raise
        finally:
            connection.close()
        # rowcount не підходить: при незмінених значеннях він дорівнює 0
        return self.get_by_id(note_id)

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

    def restore_note(
        self,
        note_id: int,
        title: str,
        content: str,
        created_at: datetime | None,
    ) -> str:
        """Відновлює нотатку з конкретним ID та датою (для бекапів).

        Якщо нотатка з таким ID вже існує — оновлює її (дата лишається,
        якщо в бекапі її немає). Якщо назву вже займає інша нотатка,
        відновлена отримає суфікс «(відновлено #ID)».

        Повертає назву, з якою нотатку збережено.
        """
        connection = self._get_connection()
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT id FROM notes WHERE title = %s AND id <> %s",
                    (title, note_id),
                )
                if cursor.fetchone():
                    suffix = f" (відновлено #{note_id})"
                    title = title[: 255 - len(suffix)] + suffix

                cursor.execute(
                    """
                    INSERT INTO notes (id, title, content, created_at)
                    VALUES (%s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                        title = %s,
                        content = %s,
                        created_at = COALESCE(%s, created_at)
                    """,
                    (
                        note_id, title, content, created_at or now_local(),
                        title, content, created_at,
                    ),
                )
            connection.commit()
            return title
        finally:
            connection.close()
