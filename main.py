import os
from datetime import datetime
from urllib.parse import urlencode

from backup import export_notes_to_json, import_notes_from_json
from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from note import Note
from pymysql import MySQLError
from repository import DuplicateTitleError, NoteRepository

app = FastAPI(title="Mind Card Notes Web")
templates = Jinja2Templates(directory="templates")
repo = NoteRepository()

DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

BIO_FILE = os.path.join(DATA_DIR, "bio.txt")


def get_bio() -> str:
  if os.path.exists(BIO_FILE):
    with open(BIO_FILE, "r", encoding="utf-8") as f:
      return f.read()
  return "Мій персональний лог нотаток та думок."


def save_bio(text: str):
  with open(BIO_FILE, "w", encoding="utf-8") as f:
    f.write(text)


def get_titles_map() -> dict:
  return {n.title: n.id for n in repo.get_all()}


def redirect_home(message: str | None = None, kind: str = "ok"):
  url = "/"
  if message:
    url += "?" + urlencode({"msg": message, "kind": kind})
  return RedirectResponse(url=url, status_code=303)


@app.get("/")
def index(request: Request, msg: str | None = None, kind: str = "ok"):
  notes = repo.get_all()
  notes_sorted = sorted(
      notes, key=lambda n: (n.created_at or datetime.min, n.id), reverse=True
  )
  titles_map = {n.title: n.id for n in notes}
  return templates.TemplateResponse(
      request,
      "index.html",
      context={
          "notes": notes_sorted,
          "bio_text": get_bio(),
          "titles_map": titles_map,
          "message": msg,
          "kind": kind,
      },
  )


@app.post("/bio/update")
def update_bio(bio_text: str = Form(...)):
  save_bio(bio_text)
  return redirect_home()


@app.get("/notes/new")
def create_note_form(request: Request):
  return templates.TemplateResponse(
      request, "create.html", context={"titles_map": get_titles_map()}
  )


@app.post("/notes")
def create_note(
    request: Request, title: str = Form(...), content: str = Form(...)
):
  title = title.strip()
  error = None
  status_code = 200

  if not title or not content.strip():
    error, status_code = "Заголовок і текст не можуть бути порожніми.", 422
  else:
    try:
      repo.add(title=title, content=content)
      return redirect_home()
    except DuplicateTitleError:
      error = f"Нотатка з назвою «{title}» вже існує. Оберіть іншу назву."
      status_code = 409

  return templates.TemplateResponse(
      request,
      "create.html",
      context={
          "titles_map": get_titles_map(),
          "title": title,
          "content": content,
          "error": error,
      },
      status_code=status_code,
  )


@app.get("/notes/{note_id}")
def view_note(request: Request, note_id: int):
  note = repo.get_by_id(note_id)
  if not note:
    raise HTTPException(status_code=404, detail="Нотатку не знайдено")
  return templates.TemplateResponse(
      request,
      "detail.html",
      context={"note": note, "titles_map": get_titles_map()},
  )


@app.get("/notes/{note_id}/edit")
def edit_note_form(request: Request, note_id: int):
  note = repo.get_by_id(note_id)
  if not note:
    raise HTTPException(status_code=404, detail="Нотатку не знайдено")
  return templates.TemplateResponse(
      request,
      "edit.html",
      context={"note": note, "titles_map": get_titles_map()},
  )


@app.post("/notes/{note_id}/update")
def update_note(
    request: Request,
    note_id: int,
    title: str = Form(...),
    content: str = Form(...),
):
  note = repo.get_by_id(note_id)
  if not note:
    raise HTTPException(status_code=404, detail="Нотатку не знайдено")

  title = title.strip()
  error = None
  status_code = 200

  if not title or not content.strip():
    error, status_code = "Заголовок і текст не можуть бути порожніми.", 422
  else:
    try:
      repo.update(note_id, title=title, content=content)
      return redirect_home()
    except DuplicateTitleError:
      error = f"Нотатка з назвою «{title}» вже існує. Оберіть іншу назву."
      status_code = 409

  # Повертаємо форму з тим, що ввів користувач
  edited = Note(
      note_id=note.id, title=title, content=content, created_at=note.created_at
  )
  return templates.TemplateResponse(
      request,
      "edit.html",
      context={
          "note": edited,
          "titles_map": get_titles_map(),
          "error": error,
      },
      status_code=status_code,
  )


@app.post("/notes/{note_id}/delete")
def delete_note(note_id: int):
  repo.delete(note_id)
  return redirect_home()


@app.post("/backup")
def make_backup():
  try:
    count = export_notes_to_json(repo)
  except (OSError, ValueError, MySQLError) as error:
    return redirect_home(f"Помилка бекапу: {error}", "error")
  return redirect_home(f"Бекап оновлено. Нотаток із бази записано: {count}.")


@app.post("/restore")
def restore_backup():
  try:
    restored, renamed = import_notes_from_json(repo)
  except (OSError, ValueError, MySQLError) as error:
    return redirect_home(f"Помилка відновлення: {error}", "error")

  message = f"Відновлено нотаток: {restored}."
  if renamed:
    message += f" Через збіг назв перейменовано: {len(renamed)}."
  return redirect_home(message)
