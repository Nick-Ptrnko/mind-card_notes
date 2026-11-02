class Note:

    def __init__(self, note_id: int, title: str, content: str, created_at):
        self.id: int = note_id
        self.title: str = title
        self.content: str = content
        self.created_at = created_at

    def __repr__(self) -> str:
        return f"<Note #{self.id}: {self.title}>"
