import os
from backup import export_notes_to_json, import_notes_from_json
from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from repository import NoteRepository

app = FastAPI(title="Mind Card Notes Web")
templates = Jinja2Templates(directory="templates")
repo = NoteRepository()

BIO_FILE = "bio.txt"


def get_bio() -> str:
  if os.path.exists(BIO_FILE):
    with open(BIO_FILE, "r", encoding="utf-8") as f:
      return f.read()
  return "Мій персональний лог нотаток та думок."


def save_bio(text: str):
  with open(BIO_FILE, "w", encoding="utf-8") as f:
    f.write(text)


@app.get("/")
def index(request: Request):
  notes = repo.get_all()
  notes_sorted = sorted(
      notes, key=lambda n: n.created_at if n.created_at else "", reverse=True
  )
  bio_text = get_bio()
  titles_map = {n.title: n.id for n in notes}
  return templates.TemplateResponse(
      request,
      "index.html",
      context={"notes": notes_sorted, "bio_text": bio_text, "titles_map": titles_map},
  )


@app.post("/bio/update")
def update_bio(bio_text: str = Form(...)):
  save_bio(bio_text)
  return RedirectResponse(url="/", status_code=303)


@app.get("/notes/new")
def create_note_form(request: Request):
  all_notes = repo.get_all()
  titles_map = {n.title: n.id for n in all_notes}
  return templates.TemplateResponse(
      request, "create.html", context={"titles_map": titles_map}
  )


@app.post("/notes")
def create_note(title: str = Form(...), content: str = Form(...)):
  if title.strip() and content.strip():
    repo.add(title=title, content=content)
  return RedirectResponse(url="/", status_code=303)


@app.get("/notes/{note_id}")
def view_note(request: Request, note_id: int):
  note = repo.get_by_id(note_id)
  if not note:
    raise HTTPException(status_code=404, detail="Нотатку не знайдено")
  all_notes = repo.get_all()
  titles_map = {n.title: n.id for n in all_notes}
  return templates.TemplateResponse(
      request,
      "detail.html",
      context={"note": note, "titles_map": titles_map},
  )


@app.get("/notes/{note_id}/edit")
def edit_note_form(request: Request, note_id: int):
  note = repo.get_by_id(note_id)
  if not note:
    raise HTTPException(status_code=404, detail="Нотатку не знайдено")
  all_notes = repo.get_all()
  titles_map = {n.title: n.id for n in all_notes}
  return templates.TemplateResponse(
      request,
      "edit.html",
      context={"note": note, "titles_map": titles_map},
  )


@app.post("/notes/{note_id}/update")
def update_note(note_id: int, title: str = Form(...), content: str = Form(...)):
  repo.update(note_id, title=title, content=content)
  return RedirectResponse(url="/", status_code=303)


@app.post("/notes/{note_id}/delete")
def delete_note(note_id: int):
  repo.delete(note_id)
  return RedirectResponse(url="/", status_code=303)


@app.post("/backup")
def make_backup():
  export_notes_to_json(repo)
  return RedirectResponse(url="/", status_code=303)


@app.post("/restore")
def restore_backup():
  try:
    import_notes_from_json(repo)
  except Exception:
    pass
  return RedirectResponse(url="/", status_code=303)
