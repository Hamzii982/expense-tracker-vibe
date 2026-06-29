# Spec: Add Expense

## Overview
This step turns the `/expenses/add` stub into a working create-expense flow. The user (logged in) lands on a form, fills in amount, category, date, and an optional description, and submits. A new row is inserted into `expenses` scoped to `session["user_id"]`, and the user is redirected back to `/profile` where the new row appears in the recent-transactions table and is reflected in the summary stats and category breakdown. This is the first of three CRUD steps — once Step 7 is done the user can write data; Step 8 (edit) and Step 9 (delete) follow the same shape and the helpers added here should make them small additions.

## Depends on
- Step 1 — Database setup. The `expenses` table exists with columns `id, user_id, amount, category, date, description, created_at`.
- Step 2 — Registration. `session["user_id"]` is set on successful registration.
- Step 3 — Login and Logout. `session["user_id"]` is set on successful login.
- Step 4 — Profile Page Design. `templates/profile.html` exists and the "Add expense" button is rendered in the user card.
- Step 5 — Backend Routes for Profile Page. `/profile` reads from `expenses`; the new row added here will appear there without further changes.
- Step 6 — Date Filter. The `/profile` route now supports date filtering. New rows should default to today's date so they fall into the "This month" / "All time" filter naturally.

## Routes
- `GET /expenses/add` — render the add-expense form — logged-in only (redirect to `/login` if not authenticated)
- `POST /expenses/add` — validate input, insert a row into `expenses`, redirect to `/profile` — logged-in only (redirect to `/login` if not authenticated)

The GET form is rendered as `templates/add_expense.html`. The POST is processed by the same view function. On success the response is a 302 redirect to `url_for("profile")`. On validation failure the form is re-rendered with an error message and a 400 status, with the user's submitted values echoed back (except the password-less fields — there's no password here, but amount/category/date/description are all safe to echo).

The "Add expense" button on `templates/profile.html` currently uses `<button type="button">` and does nothing. This step changes it to an `<a class="btn-primary" href="{{ url_for('add_expense') }}">` so the existing visual is preserved and the link becomes a real navigation target.

## Database changes
No database changes. The `expenses` table from Step 1 already has the right shape:
```
id          INTEGER PRIMARY KEY AUTOINCREMENT
user_id     INTEGER NOT NULL REFERENCES users(id)
amount      REAL    NOT NULL
category    TEXT    NOT NULL
date        TEXT    NOT NULL        -- stored as 'YYYY-MM-DD'
description TEXT                    -- nullable
created_at  TEXT    NOT NULL DEFAULT (datetime('now'))
```

`user_id` comes from `session["user_id"]` (never the form). `created_at` is set by the SQLite default. The form only supplies `amount`, `category`, `date`, and optionally `description`.

## Templates
- **Create:** `templates/add_expense.html` — extends `base.html`, loads `static/css/add_expense.css` in the `head` block. Layout: a single card-style form with the page title, a back link to `/profile`, four fields (amount, category, date, description), a primary submit button, and an error banner slot. Category is a `<select>` with a fixed option list (see Rules for the exact list). Date defaults to today. Description is a single-line text input.
- **Modify:** `templates/profile.html` — change the "Add expense" button in `.profile-user-actions` from `<button type="button" class="btn-primary">Add expense</button>` to `<a class="btn-primary" href="{{ url_for('add_expense') }}">Add expense</a>`. No other structural changes.

## Files to change
- `app.py`
  - Replace the `add_expense()` stub (currently returns a plain string) with a real view that handles both `GET` and `POST`.
  - On `GET`: render `templates/add_expense.html` with a context dict containing `today` (an ISO `YYYY-MM-DD` string for the date input default), `categories` (the list below), and a `form` dict echoing back any previously submitted values (empty on first render), plus an empty `error`.
  - On `POST`:
    - Read `amount`, `category`, `date`, `description` from `request.form`. Strip each (or coerce to `None` for `description` if blank after stripping).
    - Validate (see Rules for the full validation list). On any failure, re-render the form with the submitted values echoed, a 400 status, and a human-readable error message.
    - Open a connection with `get_db()`, run a parameterised `INSERT INTO expenses(user_id, amount, category, date, description) VALUES (?, ?, ?, ?, ?)`, commit, close.
    - Redirect to `url_for("profile")` (no flash message in this step — the visual confirmation is the new row appearing in the recent-transactions table).
  - Define a module-level constant `EXPENSE_CATEGORIES` (tuple of strings) so the list is shared by the view, the template, and any future edit form. Suggested values: `("Food", "Transport", "Bills", "Health", "Entertainment", "Shopping", "Other")`. These match the categories already used by the seeded data so a freshly added row will colour correctly in the category breakdown.
- `templates/profile.html` — see Templates above.
- `static/css/add_expense.css` (new file) — see Files to create.

## Files to create
- `templates/add_expense.html`
- `static/css/add_expense.css` — per-page override loaded after `style.css` via the `{% block head %}` link, matching the convention from `landing.css` / `profile.css` / `analytics.css`. Defines the layout of the add-expense card (a centred single-column form, max-width around 560px, padding, border-radius matching the existing cards), the field rows, the error banner style, and the back link. Reuses `--accent`, `--max-width`, the existing button classes (`.btn-primary`, `.btn-ghost`), and the form-input baseline from `style.css`. **No new hex values** — every colour, font, and spacing token references an existing `var(--…)` in `style.css`.

## New dependencies
No new dependencies. The route uses only `sqlite3` (already imported in `app.py`) and stdlib `datetime.date` (already imported).

## Rules for implementation
- No SQLAlchemy or ORMs — raw `sqlite3` via `database.db.get_db()`.
- Parameterised queries only — the `INSERT` uses `?` placeholders for all five values. `user_id` is bound from `session["user_id"]`, never from `request.form`.
- Passwords hashed with werkzeug — N/A for this step, no passwords involved. (Kept here for parity with the global Rules in other specs.)
- Use CSS variables — never hardcode hex values in `add_expense.css` or `add_expense.html`. All colours, fonts, radii, and spacing come from `style.css`'s `:root` tokens.
- All templates extend `base.html` — `add_expense.html` does so via `{% extends "base.html" %}`.
- The `EXPENSE_CATEGORIES` tuple is defined once in `app.py` and passed to the template as `categories`. Do not hardcode the option list in the template. The template renders them with a loop and an empty default option (`<option value="" disabled selected hidden>`) so the placeholder text "Select a category" appears until a choice is made.
- Validation (all errors return a 400 and re-render the form with submitted values):
  1. **Amount** — must parse as a positive float. Reject empty, non-numeric, zero, and negative. Two-decimal-place precision is fine (e.g. `12.50`); no scientific notation, no commas, no currency symbol. Suggested max: `1_000_000.00` — anything above that is rejected as a sanity cap.
  2. **Category** — must be present in `EXPENSE_CATEGORIES`. Reject anything else (this prevents arbitrary strings from being inserted and keeps the category breakdown colours consistent).
  3. **Date** — must be a valid `YYYY-MM-DD` (use `date.fromisoformat`; any `ValueError` / `TypeError` means invalid). Must be `<= today` — future-dated expenses are not allowed in this step. Dates older than ten years are allowed (the user might be back-filling an expense they forgot to log).
  4. **Description** — optional. After `.strip()`, if the result is empty, store `None`; otherwise store the stripped string. Max length 200 characters (truncate or reject — pick one; reject is simpler and keeps the UI honest). Empty / whitespace-only is not an error.
  5. Submitting with a missing `user_id` in the session is treated as "not logged in" → 302 to `/login`. The login redirect happens before any form processing.
- Error messages are short, human, and lower-case to match the existing register/login error copy (e.g. `"amount must be greater than 0"`, `"please pick a category"`, `"date can't be in the future"`).
- The `description` field, when present, is stored as a plain string. No HTML, no markdown, no link parsing. The template renders it with `{{ tx.description }}` (Jinja auto-escapes), so XSS is not a concern — but the spec still forbids storing anything other than the user's literal text.
- The form has no JS. Plain submit, server-side redirect. Do not introduce client-side validation that diverges from the server-side rules.
- The category colour classes (`.cat-badge--<name>`, `.cat-bar--<name>`) already exist in `style.css` / `profile.css` for the seven categories above. Adding a new category in the future would require adding a colour class — out of scope for this step, but the spec flags it.
- The "Add expense" button on the profile page keeps its `class="btn-primary"` styling and just changes from a non-functional `<button type="button">` to a real `<a>` link. The visual is identical.
- The success path is a 302 to `/profile` (no filter args), so the new row appears in the default "All time" view. If the user came from a filtered view (e.g. clicked a future "Add expense" link from within a month), the redirect would need to preserve those args — but that link doesn't exist yet, so this step keeps the redirect simple.
- Do not touch the seeded demo data, `database/db.py`, or any other route's behaviour.
- Do not add a flash-message framework. Step 7 ships without flash messages; if a future step wants a "Expense added" toast, it can add one globally.

## Definition of done
- Visiting `/expenses/add` while logged out redirects to `/login`.
- Visiting `/expenses/add` while logged in renders a form with: amount (number), category (select with 7 options + a disabled default), date (defaults to today), description (text, optional), a primary "Add expense" submit button, and a back link to `/profile`.
- Submitting a valid form (e.g. amount `15.50`, category `Food`, today's date, description `Coffee`) inserts exactly one row into `expenses` with the supplied values, `user_id = session["user_id"]`, and the default `created_at`. The response is a 302 to `/profile`.
- After the redirect, the new row appears in the recent-transactions table on `/profile` (with the date, description, category, and amount rendered), the summary stats (`total_spent`, `txn_count`, `top_category`, `avg_monthly`) all reflect the new row when no date filter is active, and the category breakdown shows the new amount in the matching row.
- Submitting with `amount` empty / non-numeric / zero / negative / above the sanity cap re-renders the form with a 400 and the appropriate error message; no row is inserted.
- Submitting with `category` empty or not in `EXPENSE_CATEGORIES` re-renders with a 400 and the appropriate error; no row is inserted.
- Submitting with `date` empty / malformed / in the future re-renders with a 400 and the appropriate error; no row is inserted.
- Submitting with `description` empty / whitespace-only stores `NULL` in the `description` column (verified by inspecting the row); submitting with a 200+ character description re-renders with a 400 and an error; submitting with a normal description stores the trimmed string.
- The submitted (invalid) values are echoed back into the form fields after a validation failure, except: `amount` is echoed as a string (not reformatted), `category` re-selects the matching `<option>`, `date` re-populates the input, and `description` re-populates the text input. The user does not have to re-type everything.
- The "Add expense" button on `/profile` is now a working link to `/expenses/add` (verified by clicking it from the dashboard and landing on the form).
- No new dependencies were added to `requirements.txt` (or wherever deps live in this repo).
- No `INSERT` uses string interpolation; all five values are bound via `?` placeholders. `user_id` is bound from `session`, not from the form.
- The add-expense form is keyboard-navigable: tabbing reaches amount, category, date, description, submit, back link, in that order. Each field has an associated `<label>`.
- The app still starts on port 5001 with `python app.py`. Register/login/logout/profile still work; the seed data still loads.
- Running `python -c "from app import app; c = app.test_client()"` plus a `POST /expenses/add` with a logged-in session and a valid body returns a 302; the same call with an invalid body returns a 400.
