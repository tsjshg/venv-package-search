# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Running the app

```shell
python3 app.py
```

The server starts at http://localhost:8765. Override the port with `PORT=<n> python3 app.py`.

## Architecture

This is a single-file Python app (`app.py`) with zero external dependencies — only stdlib (`http.server`, `json`, `os`, `re`, `urllib`).

**Startup flow:** `main()` calls `load_packages()` to scan all venvs and build an in-memory index (`Handler.index`), then starts `HTTPServer`. The index is built once at startup and never refreshed.

**Package index:** `load_packages()` walks each directory in `VENV_SEARCH_DIRS`, finds subdirs containing a `lib/` folder (venv heuristic), then scans `site-packages` for `*.dist-info` directories. Package names are normalized to lowercase with `-` and `.` replaced by `_` so search is fuzzy across naming conventions.

**Request handling:** `Handler.do_GET` serves two routes:
- `GET /api/search?q=<term>` — substring match against normalized package keys, returns JSON array
- `GET /` — returns the inline HTML string (`HTML` constant at the top of the file)

**Frontend:** The entire UI is an inline HTML string in the `HTML` constant. It uses vanilla JS with a 250 ms debounced `fetch` to `/api/search`.

## Configuring venv search paths

Edit `VENV_SEARCH_DIRS` at the top of `app.py` to add or change which directories are scanned for virtual environments.
