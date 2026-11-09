import json
from repository import NoteRepository


def export_notes_to_json(
    repo: NoteRepository, filename: str = "mind_card_backup.json"
) -> int:
    """Експортує всі нотатки з бази у JSON-файл.

    Повертає кількість експортованих нотаток.
    """
    notes = repo.get_all()
    data = [
        {
            "id": note.id,
            "title": note.title,
            "content": note.content,
            "created_at": note.created_at.strftime("%Y-%m-%d %H:%M:%S")
            if note.created_at
            else None,
        }
        for note in notes
    ]

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

    return len(data)


def import_notes_from_json(
    repo: NoteRepository, filename: str = "mind_card_backup.json"
) -> int:
    """Відновлює нотатки з JSON-файлу в базу даних.

    Повертає кількість відновлених нотаток.
    """
    try:
        with open(filename, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError(f"Файл бекапу '{filename}' не знайдено.")
    except json.JSONDecodeError:
        raise ValueError(f"Пошкоджений формат JSON у файлі '{filename}'.")

    count = 0
    for item in data:
        repo.restore_note(
            note_id=item["id"],
            title=item["title"],
            content=item["content"],
            created_at=item["created_at"],
        )
        count += 1

    return count
