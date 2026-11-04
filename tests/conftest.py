import os
from dotenv import load_dotenv
import pytest
from repository import NoteRepository

load_dotenv()

# Перенаправляємо репозиторій на тестову базу даних
os.environ["DB_NAME"] = "mind_card_notes_test"


@pytest.fixture(autouse=True)
def clean_database():
    """Очищає таблицю notes перед виконанням кожного тесту"""
    repo = NoteRepository()
    connection = repo._get_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute("TRUNCATE TABLE notes")
        connection.commit()
    finally:
        connection.close()
    yield
