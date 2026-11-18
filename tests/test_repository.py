import pytest

from repository import DuplicateTitleError, NoteRepository

from datetime import timedelta

from repository import now_local

def test_add_uses_app_timezone():
    repo = NoteRepository()
    note = repo.add("Часовий пояс", "Текст")

    assert abs(note.created_at - now_local()) < timedelta(seconds=5)

def test_add_and_get_note():
    repo = NoteRepository()

    # Створення
    created_note = repo.add("Перша нотатка", "Вміст першої нотатки")
    assert created_note.id is not None
    assert created_note.title == "Перша нотатка"

    # Отримання за ID
    fetched_note = repo.get_by_id(created_note.id)
    assert fetched_note is not None
    assert fetched_note.title == "Перша нотатка"
    assert fetched_note.content == "Вміст першої нотатки"


def test_get_all_notes():
    repo = NoteRepository()
    repo.add("Нотатка 1", "Текст 1")
    repo.add("Нотатка 2", "Текст 2")

    notes = repo.get_all()
    assert len(notes) == 2


def test_get_all_is_ordered_by_id():
    repo = NoteRepository()
    for i in range(5):
        repo.add(f"Нотатка {i}", "Текст")

    ids = [n.id for n in repo.get_all()]
    assert ids == sorted(ids)


def test_update_note():
    repo = NoteRepository()
    note = repo.add("Старий заголовок", "Старий текст")

    updated_note = repo.update(
        note.id, "Новий заголовок", "Новий змінений текст"
    )
    assert updated_note.title == "Новий заголовок"
    assert updated_note.content == "Новий змінений текст"


def test_update_with_same_values_returns_note():
    repo = NoteRepository()
    note = repo.add("Заголовок", "Текст")

    assert repo.update(note.id, "Заголовок", "Текст") is not None


def test_update_missing_note_returns_none():
    repo = NoteRepository()
    assert repo.update(999, "Заголовок", "Текст") is None


def test_delete_note():
    repo = NoteRepository()
    note = repo.add("Видалити мене", "Текст")

    success = repo.delete(note.id)
    assert success is True

    # Перевіряємо, що нотатка дійсно зникла
    deleted_note = repo.get_by_id(note.id)
    assert deleted_note is None


def test_title_must_be_unique():
    repo = NoteRepository()
    repo.add("Унікальна", "Текст A")

    with pytest.raises(DuplicateTitleError):
        repo.add("Унікальна", "Текст B")

    assert len(repo.get_all()) == 1


def test_update_to_existing_title_fails():
    repo = NoteRepository()
    repo.add("Перша", "Текст")
    second = repo.add("Друга", "Текст")

    with pytest.raises(DuplicateTitleError):
        repo.update(second.id, "Перша", "Текст")

    assert repo.get_by_id(second.id).title == "Друга"
