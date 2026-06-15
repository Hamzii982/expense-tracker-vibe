# Spec: Login and Logout

## Overview
This step turns the existing `/login` route from a static render into a working authentication flow, and replaces the `/logout` placeholder with a real session-ending handler. The user submits their email and password; the app looks the user up case-insensitively, verifies the password with `werkzeug.security.check_password_hash`, and on success stores `user_id` in the session and redirects to `/profile`. `/logout` clears the session and redirects to the landing page. Together with Step 2, this gives the app a complete auth round-trip: register → login → access protected pages → logout. Step 4 (Profile) and beyond can now assume `session["user_id"]` is a trustworthy indicator of who is logged in.

## Depends on
- Step 1 — Database Setup. The `users` table (`id`, `name`, `email`, `password_hash`) must exist.
- Step 2 — Registration. The Flask `SECRET_KEY` and `session` plumbing must already be in place, and `check_password_hash` must already be imported in `app.py` (it was pre-imported in Step 2 specifically so this step wouldn't churn the import block).

## Routes
- `GET /login` — render the existing `login.html` form — public
- `POST /login` — validate input, look up user, verify password, set session, redirect — public
- `GET /logout` — clear `session`, redirect to landing — public (any visitor can hit it; no-op if not logged in)

No other routes change. The post-login redirect target is `/profile` (currently the Step 4 placeholder). The post-logout redirect target is `/`. The route table does not gain any new entries.

The decision to keep `/logout` as `GET` (not `POST`) is deliberate: the project has no CSRF token system yet, a GET is a simpler teaching surface, and the only thing it can do is drop the current session cookie. A `POST` form for logout (with CSRF) is a sensible later improvement and is called out in the rules below.

## Database changes
None. The `users` table from Step 1 already has everything login needs. The email lookup uses `lower(email) = lower(?)` so `Alice@x.com` and `alice@x.com` collide at lookup, matching the registration case-insensitivity rule. If the email does not exist, the route renders a generic "invalid email or password" message rather than "no such user" — this avoids leaking which emails are registered.

## Templates
- **Modify:** `templates/login.html` — no structural changes; the template already posts to `/login` and renders `{{ error }}` when set. (Step 2 deliberately deferred the flash-message refactor; this step picks it up. See "Templates" notes below.)
- **Modify:** `templates/base.html` — add a `flash` block placeholder so future steps have a single home for one-off messages. For this step the block is empty by default; it exists so login and registration can share a common pattern from Step 4 onward.

The inline `{{ error }}` pattern is what both `/register` (Step 2) and `/login` (this step) keep for now — it works, it matches the existing CSS (`.auth-error`), and switching to flashed messages is a pure refactor with no behaviour change. Doing the refactor here would touch Step 2 as well, and that is out of scope for a "make login work" step.

## Files to change
- `app.py`
  - Replace the `login()` view so it handles both `GET` (render) and `POST` (verify credentials, set session, redirect)
  - Replace the `logout()` placeholder with a real implementation that calls `session.clear()` and redirects to `url_for("landing")`
  - POST handler on `/login`: read `email` and `password` from `request.form`, validate presence, look up user case-insensitively, call `check_password_hash`, set `session["user_id"]`, redirect to `url_for("profile")`
  - No new imports needed — `check_password_hash`, `session`, `request`, `redirect`, `url_for` are all already in scope
- `templates/base.html`
  - Add an empty `{% block flash %}{% endblock %}` immediately inside `<main class="main-content">`, before `{% block content %}`, so future flashed-message support has a dedicated hook. This step writes nothing to it.

## Files to create
None. All needed CSS classes (`.auth-section`, `.auth-container`, `.auth-card`, `.form-group`, `.form-input`, `.btn-submit`, `.auth-error`, `.auth-switch`) are already defined in `static/css/style.css`. No new JS, no new templates, no new stylesheets, no helpers.

## New dependencies
No new pip packages. `werkzeug.security.check_password_hash` is already imported (since Step 2).

## Rules for implementation
- No SQLAlchemy or ORMs. Use `sqlite3` via `database.db.get_db()`.
- Parameterised queries only — every `?` placeholder is non-negotiable, including the email-lookup `SELECT`.
- Passwords verified with `werkzeug.security.check_password_hash` only. Never compare hashes with `==`, never compare plaintexts.
- Email lookup is case-insensitive (`WHERE lower(email) = lower(?)`) so login matches the registration collision rule. The stored hash is checked against the user's submitted password verbatim — hashes are case-sensitive and that's fine.
- Validation rules, in order, return to the form on the first failure with a short, human message:
  1. Both `email` and `password` are present and non-empty after `.strip()`. Failure message: `"all fields are required"`.
  2. (No email-shape check at login — that is a registration concern. A malformed email simply won't match any row, and the "invalid email or password" message covers it. Keeping the login POST small and honest about what it's doing.)
- Authentication outcome — exactly one error path: if the email is not found OR `check_password_hash` returns `False`, render the form with the same generic message `"invalid email or password"`. Do not distinguish "no such user" from "wrong password" in the response; doing so lets an attacker probe which emails are registered.
- Reuse the existing form's `{{ error }}` rendering — set the view's `error` context variable. Do not introduce `flash()` in this step (see Templates note).
- Use CSS variables — never hardcode hex values. The form already uses the auth-shell classes, so this is automatic unless new styling is added.
- All templates extend `base.html` (no new templates are created).
- `session.clear()` (not `session.pop("user_id")`) on logout so any other session keys added by future steps are also dropped in one call.
- Logout is `GET` for this step. A note for future work: switching to `POST` with a CSRF token is the right hardening, but it requires a CSRF story the project does not have yet, and a `GET` logout with an idempotent no-op-when-not-logged-in behaviour is acceptable for a teaching project at this stage.
- `app.secret_key` was set in Step 2; do not re-set it. `check_password_hash` was pre-imported in Step 2; do not re-add the import.

## Definition of done
- `GET /login` renders the existing form with no behavioural change.
- `POST /login` with the seeded demo credentials (`demo@spendly.com` / `demo123`) sets `session["user_id"]` and 302-redirects to `/profile`.
- `POST /login` with valid format but an email that does not exist in `users` re-renders the form with `"invalid email or password"` and sets no session value.
- `POST /login` with valid format, existing email, and a wrong password re-renders the form with the same `"invalid email or password"` message — the response is byte-for-byte identical (or as close as the form allows) to the "no such user" case, so a probing attacker cannot tell them apart.
- `POST /login` with a missing field re-renders the form with `"all fields are required"`.
- `POST /login` with a registered email in a different casing (`DEMO@SPENDLY.COM`) and the correct password succeeds.
- After successful login, the `Set-Cookie` response header contains `session=…` (verifiable by curl or the test client).
- `GET /logout` when logged in clears the session and 302-redirects to `/`. A subsequent request to any logged-in-only page (e.g. `/profile` once Step 4 lands) finds no `user_id` in the session.
- `GET /logout` when not logged in is a no-op redirect to `/` (no error).
- A user can complete a full register → logout → login → logout round trip on the same browser/session.
- No `SELECT` or `INSERT` uses string interpolation — every query has `?` placeholders.
- The app still starts on port 5001 with `python app.py` and the database seed (demo user) is unchanged.
- `templates/base.html` now contains an empty `{% block flash %}{% endblock %}` immediately before `{% block content %}`.
- `POST /register` (Step 2) and `POST /login` (this step) share the same inline-error pattern and CSS class (`.auth-error`); no behaviour regression on either form.
