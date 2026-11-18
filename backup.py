import json
import os
import tempfile
from datetime import datetime

from repository import NoteRepository

DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)
DEFAULT_BACKUP_FILE = os.path.join(DATA_DIR, "mind_card_backup.json")
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def _note_to_dict(note) -> dict:
    return {
        "id": note.id,
        "title": note.title,
        "content": note.content,
        "created_at": note.created_at.strftime(DATE_FORMAT)
        if note.created_at
        else None,
    }


def _read_backup(filename: str) -> list[dict]:
    """Читає файл бекапу й перевіряє його структуру."""
    try:
        with open(filename, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError(f"Файл бекапу '{filename}' не знайдено.")
    except json.JSONDecodeError:
        raise ValueError(f"Пошкоджений формат JSON у файлі '{filename}'.")

    if not isinstance(data, list):
        raise ValueError(
            f"Некоректна структура файлу '{filename}': очікується список нотаток."
        )
    for item in data:
        if (
            not isinstance(item, dict)
            or not isinstance(item.get("id"), int)
            or isinstance(item.get("id"), bool)
            or not isinstance(item.get("title"), str)
            or not isinstance(item.get("content"), str)
        ):
            raise ValueError(
                f"Некоректний запис у файлі '{filename}': потрібні поля id, title, content."
            )
    return data


def _parse_date(item: dict) -> datetime | None:
    value = item.get("created_at")
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except (TypeError, ValueError):
        raise ValueError(
            f"Некоректна дата у нотатці #{item['id']}: '{value}'."
        )


def _write_atomic(filename: str, data: list[dict]) -> None:
    """Пише у тимчасовий файл і підміняє основний, щоб збій не пошкодив бекап."""
    directory = os.path.dirname(os.path.abspath(filename))
    fd, tmp_path = tempfile.mkstemp(dir=directory, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        os.chmod(tmp_path, 0o644)
        os.replace(tmp_path, filename)
    except Exception:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        raise


def export_notes_to_json(
    repo: NoteRepository, filename: str = DEFAULT_BACKUP_FILE
) -> int:
    """Дописує нотатки з бази до JSON-файлу бекапу.

    Наявні записи файлу зберігаються (зокрема нотатки, видалені з бази),
    записи з тими ж ID оновлюються поточними даними з бази.

    Повертає кількість нотаток, записаних з бази.
    """
    notes = repo.get_all()

    merged: dict[int, dict] = {}
    if os.path.exists(filename):
        # Пошкоджений файл не перезаписуємо: _read_backup кине ValueError
        for item in _read_backup(filename):
            merged[item["id"]] = item

    for note in notes:
        merged[note.id] = _note_to_dict(note)

    _write_atomic(filename, [merged[key] for key in sorted(merged)])
    return len(notes)


def import_notes_from_json(
    repo: NoteRepository, filename: str = DEFAULT_BACKUP_FILE
) -> tuple[int, list[str]]:
    """Відновлює нотатки з JSON-файлу в базу даних.

    Повертає (кількість відновлених нотаток, список назв, які довелося
    змінити через збіг із іншою нотаткою).
    """
    data = _read_backup(filename)
    # Спочатку перевіряємо всі дати, щоб не зупинитися посеред відновлення
    prepared = [(item, _parse_date(item)) for item in data]

    renamed: list[str] = []
    for item, created_at in prepared:
        stored_title = repo.restore_note(
            note_id=item["id"],
            title=item["title"],
            content=item["content"],
            created_at=created_at,
        )
        if stored_title != item["title"]:
            renamed.append(stored_title)

    return len(prepared), renamed
