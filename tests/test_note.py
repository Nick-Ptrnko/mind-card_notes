from note import Note


def test_note_initialization():
    note = Note(
        note_id=1,
        title="Тестовий заголовок",
        content="Тестовий вміст",
        created_at="2026-06-01 12:00:00",
    )

    assert note.id == 1
    assert note.title == "Тестовий заголовок"
    assert note.content == "Тестовий вміст"
    assert note.created_at == "2026-06-01 12:00:00"
    assert str(note) == "<Note #1: Тестовий заголовок>"
