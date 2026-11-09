import json
import pytest
from backup import export_notes_to_json, import_notes_from_json
from repository import NoteRepository


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
    with open(backup_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert len(data) == 2
    assert data[0]["title"] == "Тест експорту 1"
    assert data[1]["title"] == "Тест експорту 2"
    assert "id" in data[0]
    assert "created_at" in data[0]


def test_import_notes_from_json(tmp_path):
    repo = NoteRepository()

    # Підготовлюємо тестовий JSON-файл
    backup_file = tmp_path / "test_import.json"
    raw_data = [
        {
            "id": 101,
            "title": "Відновлена нотатка",
            "content": "Вміст з бекапу",
            "created_at": "2026-05-15 10:00:00",
        }
    ]

    with open(backup_file, "w", encoding="utf-8") as f:
        json.dump(raw_data, f, ensure_ascii=False)

    count = import_notes_from_json(repo, str(backup_file))

    assert count == 1

    # Перевіряємо, що нотатка опинилася в БД з правильними даними
    imported_note = repo.get_by_id(101)
    assert imported_note is not None
    assert imported_note.id == 101
    assert imported_note.title == "Відновлена нотатка"
    assert imported_note.content == "Вміст з бекапу"


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
