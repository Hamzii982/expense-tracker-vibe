# Spec: Registration

## Overview
This step turns the existing `/register` route from a static render into a working registration flow. The user submits their name, email, and password, the app hashes the password, stores the new user in the `users` table, and signs them in immediately by creating a session. After registration, the user is redirected to the dashboard landing page that subsequent steps will fill out. This step also adds the Flask `SECRET_KEY` and `session` plumbing that every later auth step depends on, so login, logout, and the rest of the app can assume sessions already work.

## Depends on
- Step 1 — Database Setup. The `users` table (`id`, `name`, `email`, `password_hash`, `created_at`) must exist with the unique email constraint in place.

## Routes
- `GET /register` — render the existing `register.html` form — public
- `POST /register` — validate input, create the user, log them in, redirect — public

No other routes change in this step. The post-registration redirect target is `/profile` (currently the Step 4 placeholder returning a plain string) — this is acceptable for now and will be replaced when the profile page is built.

## Database changes
No new tables or columns. The `users` table from Step 1 already has everything registration needs:
- `name TEXT NOT NULL`
- `email TEXT UNIQUE NOT NULL` — the unique constraint enforces "one account per email" at the database level
- `password_hash TEXT NOT NULL` — populated with `werkzeug.security.generate_password_hash`

If the email already exists, the INSERT will raise `sqlite3.IntegrityError`; the route catches this and re-renders the form with an error message rather than a 500.

## Templates
- **Modify:** `templates/register.html` — no structural changes; the template already posts to `/register` and renders `{{ error }}` when set.

No other templates change. `base.html` does not need a `flash` block yet — registration returns a single error inline rather than using flashed messages, and that pattern will be revisited in Step 3 (Login) when both forms need to share a flash pattern.

## Files to change
- `app.py`
  - Add `from flask import Flask, render_template, request, redirect, url_for, session` to the existing flask import
  - Add `from werkzeug.security import generate_password_hash, check_password_hash` (the second import is included now even though login is Step 3, so the import block doesn't churn next step — note this in a comment)
  - Set `app.secret_key` from an env var with a dev fallback (e.g. `app.secret_key = os.environ.get("SECRET_KEY") or "dev-only-change-me"`) — read once at module load
  - Add `import os` for the env-var lookup
  - Replace the `register()` view so it handles both `GET` (render) and `POST` (create user)
  - POST handler: read `name`, `email`, `password` from `request.form`, validate, insert, set `session["user_id"]`, redirect to `url_for("profile")`

## Files to create
None. All needed CSS classes (`.auth-section`, `.auth-container`, `.auth-card`, `.form-group`, `.form-input`, `.btn-submit`, `.auth-error`, `.auth-switch`) are already defined in `static/css/style.css` from the landing/auth shell work, and the existing `register.html` uses them. No new JS, no new templates, no new stylesheets.

## New dependencies
No new pip packages. `werkzeug` and `flask` are already installed.

## Rules for implementation
- No SQLAlchemy or ORMs. Use `sqlite3` via the existing `database.db.get_db()` connection.
- Parameterised queries only — every `?` placeholder in SQL is non-negotiable, including the `SELECT` that checks for an existing email.
- Passwords hashed with `werkzeug.security.generate_password_hash`. Never store plaintext, never log it.
- Email comparison is case-insensitive in the duplicate check (`SELECT ... WHERE lower(email) = lower(?)`) so `Alice@x.com` and `alice@x.com` collide. The stored value keeps the casing the user typed, matching the `seed_db` convention.
- Validation rules, in order, return to the form on the first failure with a short, human message:
  1. All three fields are present and non-empty after `.strip()`.
  2. Email contains exactly one `@` with non-empty local and domain parts (a light check — full RFC validation is out of scope for a teaching project).
  3. Password length is at least 8 characters.
- Reuse the existing form's error rendering — set the view's `error` context variable, do not introduce `flash()`.
- Use CSS variables — never hardcode hex values. The form already uses the auth-shell classes, so this is automatic unless new styling is added.
- All templates extend `base.html` (no new templates are created, so this is a no-op but noted for the spec record).
- `app.secret_key` must be set before the first request. Reading it at module load (top of `app.py`) is fine because Flask routes don't fire until `app.run()`.

## Definition of done
- `GET /register` renders the existing form with no behavioural change.
- `POST /register` with valid input creates a row in `users` whose `password_hash` is a `werkzeug` hash (not the plaintext).
- `POST /register` with a duplicate email re-renders the form with an "email already registered" message and creates no row.
- `POST /register` with a password under 8 characters re-renders the form with a "password must be at least 8 characters" message and creates no row.
- `POST /register` with missing fields re-renders the form with a "all fields are required" message and creates no row.
- After successful registration, the user is redirected (302) to `/profile` and a session cookie is set (verifiable via the `Set-Cookie` response header).
- A second registration with the same email but different casing (`Alice@x.com` after `alice@x.com`) is rejected as a duplicate.
- No `SELECT` or `INSERT` uses string interpolation — every query has `?` placeholders.
- The app still starts on port 5001 with `python app.py` and the database seed (demo user) is unchanged.
