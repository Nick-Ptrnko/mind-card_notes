# Mind Card Notes Web

A personal log of mental cards designed to recreate the original **Zettelkasten** philosophy, which often gets lost when managing complex knowledge bases in tools like Obsidian. Each mental card is meant to be compact and contain a single idea that can be recalled from memory at the moment of creation. When returning to a card later, its content should be easy to remember—or, if forgotten, easy to reconstruct.

Beyond its practical utility for taking notes and accessing them from any device via **WireGuard VPN**, this application was built specifically as a hands-on project for practicing Python development.

---

## 🛠 Tech Stack & Architecture

* **FastAPI:** Powers the web backend, routing, and form handling.
* **Jinja2:** Renders dynamic HTML templates on the server side.
* **MySQL & PyMySQL:** Used as the relational database layer. `PyMySQL` was intentionally chosen instead of an ORM to explore and practice how databases work directly through raw SQL queries (without an abstraction layer).
* **Environment Configuration (`.env`):** Sensitive credentials and database connection parameters are isolated in a `.env` file.
* **File System & `os` Module Practice:** The description text displayed on the main page is stored in `bio.txt`, and the JSON database backup/restore system is file-based—both implemented specifically to study and practice file operations and the Python `os` module.

---

## ✨ Features

* **Live Preview and Markdown:** The `marked.js` library is used for instant conversion of Markdown markup into HTML right while typing, as well as `highlight.js` for syntax highlighting of program code.
* **Custom Syntax Extensions:**
  * Autocomplete and internal linking between notes are implemented using double square bracket syntax (`[[Note Title]]`).
  * Added support for highlighting text with markers (`==text==`).
* **Responsiveness and UX:** The interface supports a dark theme, live search of notes by title "on the fly", grouping of notes by creation dates, and convenient editing of the profile description (`bio.txt`).
