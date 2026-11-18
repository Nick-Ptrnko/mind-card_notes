import os

# ВАЖЛИВО: змінну треба виставити ДО імпорту repository.
# repository.py читає DB_NAME один раз під час імпорту, а load_dotenv()
# не перезаписує вже задані змінні середовища, тож .env тут не вплине.
TEST_DB_NAME = "mind_card_notes_test"
os.environ["DB_NAME"] = TEST_DB_NAME

import pymysql
import pytest

import repository
from repository import NoteRepository

# Запобіжник: якщо repository із якоїсь причини вже імпортовано з іншою
# базою, зупиняємо всю сесію, поки нічого не стерто.
if repository.DB_CONFIG["database"] != TEST_DB_NAME:
    pytest.exit(
        f"repository підключений до '{repository.DB_CONFIG['database']}', "
        f"а не до '{TEST_DB_NAME}'. Тести зупинено, щоб не пошкодити дані.",
        returncode=2,
    )


@pytest.fixture(scope="session", autouse=True)
def ensure_test_database():
    """Створює тестову базу, якщо її ще немає (потрібне право CREATE)."""
    config = {k: v for k, v in repository.DB_CONFIG.items() if k != "database"}
    try:
        connection = pymysql.connect(**config)
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    f"CREATE DATABASE IF NOT EXISTS `{TEST_DB_NAME}` "
                    "CHARACTER SET utf8mb4"
                )
            connection.commit()
        finally:
            connection.close()
    except pymysql.MySQLError:
        # Прав на CREATE може не бути: тоді базу створюють вручну,
        # а якщо її немає, тести впадуть із зрозумілою помилкою підключення.
        pass


@pytest.fixture(autouse=True)
def clean_database(ensure_test_database):
    """Очищає таблицю notes у ТЕСТОВІЙ базі перед кожним тестом"""
    assert repository.DB_CONFIG["database"] == TEST_DB_NAME

    repo = NoteRepository()  # створює таблицю й UNIQUE, якщо їх немає
    connection = repo._get_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute("TRUNCATE TABLE notes")
        connection.commit()
    finally:
        connection.close()
    yield
