import json
from datetime import datetime

import pytest

from backup import export_notes_to_json, import_notes_from_json
from repository import NoteRepository


def _write_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)


def _read_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def test_export_notes_to_json(tmp_path):
    repo = NoteRepository()
    repo.add("Тест експорту 1", "Текст 1")
    repo.add("Тест експорту 2", "Текст 2")

    # Створюємо шлях до тимчасового файлу
    backup_file = tmp_path / "test_export.json"

    count = export_notes_to_json(repo, str(backup_file))

    assert count == 2
    assert backup_file.exists()

    # Перевіряємо вміст JSON-файлу
    data = _read_json(backup_file)

    assert len(data) == 2
    assert data[0]["title"] == "Тест експорту 1"
    assert data[1]["title"] == "Тест експорту 2"
    assert "id" in data[0]
    assert "created_at" in data[0]


def test_export_appends_to_existing_backup(tmp_path):
    repo = NoteRepository()
    backup_file = tmp_path / "append.json"

    old_note = repo.add("Стара", "Текст")
    export_notes_to_json(repo, str(backup_file))

    # Видаляємо нотатку з бази й додаємо нову: стара має лишитися у файлі
    repo.delete(old_note.id)
    repo.add("Нова", "Текст 2")
    export_notes_to_json(repo, str(backup_file))

    titles = [item["title"] for item in _read_json(backup_file)]
    assert titles == ["Стара", "Нова"]


def test_export_updates_entry_with_same_id(tmp_path):
    repo = NoteRepository()
    backup_file = tmp_path / "update.json"

    note = repo.add("Заголовок", "Старий текст")
    export_notes_to_json(repo, str(backup_file))

    repo.update(note.id, "Заголовок", "Новий текст")
    export_notes_to_json(repo, str(backup_file))

    data = _read_json(backup_file)
    assert len(data) == 1
    assert data[0]["content"] == "Новий текст"


def test_export_does_not_overwrite_corrupted_backup(tmp_path):
    repo = NoteRepository()
    repo.add("Нотатка", "Текст")
    backup_file = tmp_path / "corrupted.json"
    backup_file.write_text("{invalid json structure", encoding="utf-8")

    with pytest.raises(ValueError):
        export_notes_to_json(repo, str(backup_file))

    assert backup_file.read_text(encoding="utf-8") == "{invalid json structure"


def test_import_notes_from_json(tmp_path):
    repo = NoteRepository()

    # Підготовлюємо тестовий JSON-файл
    backup_file = tmp_path / "test_import.json"
    _write_json(
        backup_file,
        [
            {
                "id": 101,
                "title": "Відновлена нотатка",
                "content": "Вміст з бекапу",
                "created_at": "2026-05-15 10:00:00",
            }
        ],
    )

    restored, renamed = import_notes_from_json(repo, str(backup_file))

    assert restored == 1
    assert renamed == []

    # Перевіряємо, що нотатка опинилася в БД з правильними даними
    imported_note = repo.get_by_id(101)
    assert imported_note is not None
    assert imported_note.id == 101
    assert imported_note.title == "Відновлена нотатка"
    assert imported_note.content == "Вміст з бекапу"
    assert imported_note.created_at == datetime(2026, 5, 15, 10, 0, 0)


def test_import_preserves_creation_dates(tmp_path):
    repo = NoteRepository()
    backup_file = tmp_path / "dates.json"
    _write_json(
        backup_file,
        [
            {"id": 1, "title": "Перша", "content": "A", "created_at": "2026-05-10 09:30:00"},
            {"id": 2, "title": "Друга", "content": "B", "created_at": "2026-05-12 18:45:10"},
        ],
    )

    import_notes_from_json(repo, str(backup_file))

    assert repo.get_by_id(1).created_at == datetime(2026, 5, 10, 9, 30, 0)
    assert repo.get_by_id(2).created_at == datetime(2026, 5, 12, 18, 45, 10)
    assert len({n.created_at.date() for n in repo.get_all()}) == 2


def test_import_is_idempotent(tmp_path):
    repo = NoteRepository()
    backup_file = tmp_path / "twice.json"
    _write_json(
        backup_file,
        [{"id": 5, "title": "Нотатка", "content": "Текст", "created_at": "2026-05-10 09:30:00"}],
    )

    import_notes_from_json(repo, str(backup_file))
    import_notes_from_json(repo, str(backup_file))

    assert len(repo.get_all()) == 1


def test_import_renames_note_on_title_conflict(tmp_path):
    repo = NoteRepository()
    live = repo.add("Назва", "Жива нотатка")

    backup_file = tmp_path / "conflict.json"
    _write_json(
        backup_file,
        [{"id": 50, "title": "Назва", "content": "З бекапу", "created_at": "2026-05-10 09:30:00"}],
    )

    restored, renamed = import_notes_from_json(repo, str(backup_file))

    assert restored == 1
    assert len(renamed) == 1
    assert repo.get_by_id(live.id).content == "Жива нотатка"
    assert repo.get_by_id(50).title.startswith("Назва (відновлено")


def test_import_notes_file_not_found(tmp_path):
    repo = NoteRepository()
    non_existent_file = tmp_path / "absent.json"

    with pytest.raises(FileNotFoundError):
        import_notes_from_json(repo, str(non_existent_file))


def test_import_notes_invalid_json(tmp_path):
    repo = NoteRepository()
    corrupted_file = tmp_path / "corrupted.json"

    # Записуємо некоректний JSON
    with open(corrupted_file, "w", encoding="utf-8") as f:
        f.write("{invalid json structure")

    with pytest.raises(ValueError, match="Пошкоджений формат JSON"):
        import_notes_from_json(repo, str(corrupted_file))


def test_import_notes_invalid_structure(tmp_path):
    repo = NoteRepository()
    bad_file = tmp_path / "bad_structure.json"
    _write_json(bad_file, [{"id": 1, "title": "Без тексту"}])

    with pytest.raises(ValueError, match="Некоректний запис"):
        import_notes_from_json(repo, str(bad_file))

    assert repo.get_all() == []
