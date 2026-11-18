# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased] - 2026-11-18

### Added

- Confirmation dialogs before "Backup" and "Restore", similar to the existing one for note deletion.
- Success and error banner on the home page. Backup and restore results (including errors) are now shown to the user instead of being silently swallowed.
- `UNIQUE` constraint on `notes.title`, with an automatic migration for existing databases. If duplicate titles already exist, startup stops with a message explaining how to find them.
- `DuplicateTitleError`. Creating or renaming a note to an existing title now shows an error on the form (HTTP 409) and keeps the user's input instead of returning a 500.
- Validation of backup files: the structure (a list of objects with `id`, `title`, `content`) and every `created_at` value are checked before anything is written to the database.
- Tests for: appending to a backup, updating entries with the same id, refusing to overwrite a corrupted backup, preserved creation dates, idempotent restore, title conflicts on restore, invalid backup structure, unique titles, ordering by id, and updating with unchanged or missing notes.

### Changed

- **Backup now appends instead of overwriting.** Existing entries in the backup file are kept (including notes later deleted from the database); entries with the same id are updated with current data. To start a fresh backup, delete the file manually.
- Backup is written atomically (temporary file + `os.replace`), so a failure in the middle of a write cannot corrupt the only copy. A corrupted existing backup is never overwritten.
- `import_notes_from_json` now returns a tuple: the number of restored notes and the list of titles that had to be renamed.
- When a restored note's title is already used by a different note, it is saved with the suffix "(відновлено #ID)" instead of failing.
- On restore, a missing `created_at` no longer overwrites an existing date; a new note without a date gets the current time.
- `get_all()` now uses `ORDER BY id`, so the order of notes is deterministic.
- `restore_note` accepts a parsed `datetime` (or `None`) instead of a raw string.
- Update and create handlers trim the title and re-render the form with an error message on invalid input instead of silently ignoring it.
- The `titles_map` construction was moved into a single `get_titles_map()` helper in `main.py`.

### Fixed

- **Tests could wipe the real database.** `DB_NAME` was set after `repository` was imported, so `TRUNCATE TABLE notes` ran against the database from `.env`. It is now set before the import, a guard aborts the test session if the connection is not to the test database, and the test database is created automatically (when the user has the `CREATE` privilege).
- Restored notes could end up under a single day on the home page. Dates from the backup file are now parsed and validated and passed to MySQL as `datetime` values; a test covers notes restored onto different days.
- The home page crashed with a `TypeError` when a note had `created_at = None`. Sorting now falls back to `datetime.min` and uses the id as a tie-breaker.
- `NoteRepository.update` returned `None` when the values were unchanged (MySQL reports 0 affected rows). It now returns the note whenever it exists.
- Updating a non-existent note now returns 404 instead of silently redirecting.
- A backup file with valid JSON but an unexpected structure no longer raises an unhandled `KeyError` or `TypeError`; it produces a clear error message.
- Note creation time was shown 2 hours behind local time because MySQL `CURRENT_TIMESTAMP` uses the server timezone (UTC in Docker). The application now sets `created_at` itself in the configured timezone (`APP_TIMEZONE`, default `Europe/Kyiv`); `tzdata` was added to requirements. Existing rows must be shifted once (see migration notes).
### Migration notes

- On first start, a unique index `uq_notes_title` is added to the existing `notes` table. If the table contains duplicate titles, rename them first. To find them, run:

```sql
SELECT title, COUNT(*) FROM notes GROUP BY title HAVING COUNT(*) > 1;
```

- If the database user cannot create databases, create the test database once manually:

```sql
CREATE DATABASE mind_card_notes_test CHARACTER SET utf8mb4;
GRANT ALL ON mind_card_notes_test.* TO 'your_user'@'%';
```

- MySQL compares titles case-insensitively by default, so "Note" and "note" are treated as duplicates.
- Files changed: `repository.py`, `backup.py`, `main.py`, `templates/index.html`, `templates/create.html`, `templates/edit.html`, `tests/conftest.py`, `tests/test_repository.py`, `tests/test_backup.py`.
