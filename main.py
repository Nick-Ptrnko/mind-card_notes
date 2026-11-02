from note import Note


# Клас-Репозиторій
class NoteRepository:

    def __init__(self):
        self._storage: dict[int, Note] = {}
        self._next_id: int = 1

    def add(self, title: str, content: str) -> Note:
        note = Note(note_id=self._next_id, title=title, content=content)
        self._storage[note.id] = note
        self._next_id += 1
        return note

    def get_all(self) -> list[Note]:
        return list(self._storage.values())

    def get_by_id(self, note_id: int) -> Note | None:
        return self._storage.get(note_id)

    def update(self, note_id: int, title: str, content: str) -> Note | None:
        note = self.get_by_id(note_id)
        if note:
            note.title = title
            note.content = content
            return note
        return None

    def delete(self, note_id: int) -> bool:
        if note_id in self._storage:
            del self._storage[note_id]
            return True
        return False


# --- ІНТЕРАКТИВНЕ КЕРУВАННЯ В КОНСОЛІ ---
if __name__ == "__main__":
    repo = NoteRepository()

    while True:
        print("\n=== МЕНЮ ===")
        print("1. Створити нотатку")
        print("2. Показати всі нотатки")
        print("3. Прочитати нотатку за ID")
        print("4. Редагувати нотатку")
        print("5. Видалити нотатку")
        print("0. Вийти")

        choice = input("Виберіть дію: ").strip()

        if choice == "1":
            title = input("Введіть заголовок: ").strip()
            content = input("Введіть текст нотатки: ").strip()
            if title and content:
                new_note = repo.add(title=title, content=content)
                print(f" Успішно створено нотатку #{new_note.id}")
            else:
                print(" Заголовок і текст не можуть бути порожніми!")

        elif choice == "2":
            notes = repo.get_all()
            if not notes:
                print(" Список нотаток порожній.")
            else:
                print("\n--- Список усіх нотаток ---")
                for note in notes:
                    print(f"#{note.id} | {note.title} ({note.created_at})")

        elif choice == "3":
            raw_id = input("Введіть ID нотатки: ").strip()
            if raw_id.isdigit():
                note_id = int(raw_id)
                note = repo.get_by_id(note_id)
                if note:
                    print(f"\n--- Нотатка #{note.id} ---")
                    print(f"Заголовок: {note.title}")
                    print(f"Текст:     {note.content}")
                    print(f"Створено:  {note.created_at}")
                else:
                    print(f" Нотатку з ID {note_id} не знайдено.")
            else:
                print(" ID має бути числом!")

        elif choice == "4":
            raw_id = input("Введіть ID нотатки для редагування: ").strip()
            if raw_id.isdigit():
                note_id = int(raw_id)
                note = repo.get_by_id(note_id)
                if note:
                    print(
                        f"Поточний заголовок: {note.title}\nПоточний текст: {note.content}"
                    )
                    title = input(
                        "Введіть новий заголовок (або залиште порожнім, щоб не змінювати): "
                    ).strip()
                    content = input(
                        "Введіть новий текст (або залиште порожнім, щоб не змінювати): "
                    ).strip()

                    updated_title = title if title else note.title
                    updated_content = content if content else note.content

                    repo.update(
                        note_id, title=updated_title, content=updated_content
                    )
                    print(f" Успішно оновлено нотатку #{note_id}")
                else:
                    print(f" Нотатку з ID {note_id} не знайдено.")
            else:
                print(" ID має бути числом!")

        elif choice == "5":
            raw_id = input("Введіть ID нотатки для видалення: ").strip()
            if raw_id.isdigit():
                note_id = int(raw_id)
                if repo.delete(note_id):
                    print(f" Нотатку #{note_id} успішно видалено.")
                else:
                    print(f" Нотатку з ID {note_id} не знайдено.")
            else:
                print(" ID має бути числом!")

        elif choice == "0":
            print("До побачення!")
            break

        else:
            print("Невідома команда, спробуйте ще раз.")
