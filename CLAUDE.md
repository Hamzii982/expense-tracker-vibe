# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

**Spendly** — a Flask-based personal expense tracker. A teaching/learning project structured as a sequence of build steps. The landing page, auth shells, and legal pages are done; the data layer (Step 1) and CRUD features (Steps 3–9) are stubbed and have not been built yet.

## Common commands

```bash
# Activate the venv (Windows PowerShell)
.\venv\Scripts\Activate.ps1

# Run dev server (debug mode, port 5001)
python app.py

# Run tests
pytest

# Render any route once without a browser, to confirm it 200s
python -c "from app import app; c = app.test_client(); print(c.get('/').status_code)"
```

The dev server runs on **port 5001** (not the Flask default 5000) and is started directly from `app.py` with `debug=True`. There is no separate `flask run` invocation in this repo.

## Architecture

**`app.py`** — Single Flask app, all routes defined here. Implemented: `/`, `/register`, `/login`, `/terms`, `/privacy`. Placeholder stubs (return a plain string) for `/logout`, `/profile`, `/expenses/add`, `/expenses/<id>/edit`, `/expenses/<id>/delete` — these are tagged with "coming in Step N" comments and correspond to the numbered build steps in the curriculum.

**`database/`** — SQLite layer. `db.py` is currently empty other than a comment block describing the three functions students must implement: `get_db()` (returns a SQLite connection with `row_factory` and foreign keys enabled), `init_db()` (creates tables via `CREATE TABLE IF NOT EXISTS`), `seed_db()` (development sample data). The DB file (`expense_tracker.db`) is gitignored.

**`templates/`** — Jinja2 templates, all extend `base.html`. The base template owns the navbar, footer, and Google Fonts link. Templates that need page-specific styles or scripts use the `head` and `scripts` blocks:
```html
{% block head %}<link rel="stylesheet" href="{{ url_for('static', filename='css/landing.css') }}">{% endblock %}
...
{% block scripts %}<script src="{{ url_for('static', filename='js/landing.js') }}"></script>{% endblock %}
```

**`static/css/style.css`** — Global stylesheet. Defines CSS custom properties on `:root` (colors, fonts, `--max-width: 1200px`), the reset, navbar, footer, `.hero` (originally a 2-col grid — see "Landing page override" below), `.features`, `.cta-section`, `.legal-section` (for terms/privacy), and the `.mock-card` used on the landing page. **Do not modify global selectors** when adding per-page styles — use a per-page override file instead, or the cascade order will surprise you.

**`static/css/landing.css`** — Per-page override loaded *after* `style.css` via the `head` block. It neutralises several global rules that were designed for an earlier hero layout:
- `.hero { display: block; max-width: 100%; margin: 0; }` — kills the global `display: grid; grid-template-columns: 1fr 1fr;` and the 1200px cap
- Inside `@media (max-width: 900px)`, `.hero-visual { display: flex; }` re-shows the mock card (the global rule hides it on tablet/mobile)

When adding new page-level overrides, follow the same pattern: new file in `static/css/`, loaded via `{% block head %}`.

**`static/js/landing.js`** — Vanilla JS for the "See how it works" YouTube modal on the landing page. No frameworks. Notable detail: clearing `iframe.src = ""` on close is what actually stops YouTube playback — autoplay iframes keep playing as long as the iframe document is loaded. The YouTube video ID is a placeholder (`dQw4w9WgXcQ`) at the top of the file; swap it for the real one later. `main.js` is currently a placeholder where future global JS will go.

## Design system conventions

- **Colors / fonts** — always reference via the `var(--…)` custom properties in `style.css`. Brand green is `--accent` (`#1a472a`), used for the italic emphasis in hero headlines and link hovers.
- **Buttons** — pill-shaped (`border-radius: 999px`). Primary action uses `.btn-primary` (filled green) or `.btn-primary-arrow` (filled ink-black, used on the landing hero). Secondary action uses `.btn-ghost` (outlined).
- **No icon fonts / no JS frameworks** — the project deliberately ships vanilla HTML, CSS, and JS. If you're tempted to add a dependency, don't.

## Git conventions

Commit messages are scoped and lowercase: `landing: <thing>`, `chore: <thing>`, etc. The recent log is exclusively landing-page work — that work is done; new tasks should pick a different scope prefix that matches the area (e.g. `auth:`, `expenses:`, `db:`).

## Things to watch out for

- The `Screenshot *.png` at repo root is a reference mockup for the landing page redesign, gitignored. Don't commit similar reference images — add them to `.gitignore` (`screenshots/`) instead.
- The Flask dev server is started from the repo root as `python app.py`. The import path relies on `app.py` being on `PYTHONPATH` (which is true when run from the repo root inside the venv).
- `database/db.py` is intentionally a stub with comments describing what students will write. Do not fill it in as part of unrelated work.
</content>
</invoke>