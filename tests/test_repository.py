from repository import NoteRepository


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


def test_update_note():
    repo = NoteRepository()
    note = repo.add("Старий заголовок", "Старий текст")

    updated_note = repo.update(
        note.id, "Новий заголовок", "Новий змінений текст"
    )
    assert updated_note.title == "Новий заголовок"
    assert updated_note.content == "Новий змінений текст"


def test_delete_note():
    repo = NoteRepository()
    note = repo.add("Видалити мене", "Текст")

    success = repo.delete(note.id)
    assert success is True

    # Перевіряємо, що нотатка дійсно зникла
    deleted_note = repo.get_by_id(note.id)
    assert deleted_note is None
