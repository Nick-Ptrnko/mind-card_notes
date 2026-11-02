from datetime import datetime


class Note:

    def __init__(self, note_id: int, title: str, content: str):
        self.id: int = note_id
        self.title: str = title
        self.content: str = content
        self.created_at: str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def __repr__(self) -> str:
        return f"<Note #{self.id}: {self.title}>"
