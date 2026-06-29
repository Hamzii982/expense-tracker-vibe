# Spec: Edit Expense

## Overview
This step turns the `/expenses/<id>/edit` stub into a working edit-expense flow, the second of three CRUD steps after Step 7 (add) and before Step 9 (delete). A logged-in user visits the route for one of their own expenses, sees a form pre-filled with the current values, changes one or more fields, and submits. The row is updated in `expenses`, scoped to `session["user_id"]`, and the user is redirected back to `/profile` where the edited row reflects the new values. The form is the same shape as the add-expense form (amount / category / date / description), the validation rules are identical, and the route is ownership-checked: if the expense belongs to a different user, the request 404s — students can't peek at or tamper with other people's data.

## Depends on
- Step 1 — Database setup. The `expenses` table exists with columns `id, user_id, amount, category, date, description, created_at`.
- Step 2 — Registration. `session["user_id"]` is set on successful registration.
- Step 3 — Login and Logout. `session["user_id"]` is set on successful login.
- Step 5 — Backend Routes for Profile Page. `/profile` reads from `expenses`; an edited row will appear with its new values without further changes.
- Step 6 — Date Filter. The `/profile` route supports date filtering. Editing a row's date may move it in or out of the active filter — that's a feature, not a bug, and is the user's responsibility to manage.
- Step 7 — Add Expense. The `EXPENSE_CATEGORIES` tuple and the add-expense template already exist; the edit template mirrors the add template's layout and shares the same category list. Validation rules in this step must match Step 7 exactly so behaviour is consistent across create and update.

## Routes
- `GET /expenses/<id>/edit` — load the expense (ownership-checked against `session["user_id"]`), render the edit form pre-filled with the current values — logged-in only
- `POST /expenses/<id>/edit` — validate input, update the row in `expenses`, redirect to `/profile` — logged-in only

Both verbs handled by the same `edit_expense(id)` view. The GET response is `200` with `templates/edit_expense.html`. The POST success path is a `302` to `url_for("profile")`. The POST validation-failure path re-renders the form with a `400`, the submitted values echoed back, and a human-readable error. Both verbs require a logged-in session; an unauthenticated request is a `302` to `/login` before the form is processed.

If the `id` in the URL doesn't exist, **or** belongs to a different user, the route returns `404` (renders `templates/404.html` if present, otherwise the Flask default 404 page). This is ownership enforcement, not a UX nicety — a user must not be able to load the edit form for someone else's expense, and a user must not be able to update it via `POST` either. The check is the same single query on both verbs: `SELECT ... FROM expenses WHERE id = ? AND user_id = ?`. If that returns no row, return `abort(404)`.

The route does **not** accept an `id` of zero or negative — `<int:id>` in the URL converter already filters those out, returning a Flask 404 routing error. No additional check needed.

The route does **not** preserve the date filter from `/profile` in the redirect — Step 7 established that "Add expense" goes to `All time` on success, and this step follows the same pattern. A future "edited from a filtered view" feature is out of scope.

## Database changes
No database changes. The `expenses` table from Step 1 has the right shape. The update writes to `amount`, `category`, `date`, `description` only — `id`, `user_id`, and `created_at` are immutable from this view. `description` is set to `NULL` when the user submits an empty / whitespace-only string, matching Step 7.

The exact update statement:
```sql
UPDATE expenses
   SET amount = ?, category = ?, date = ?, description = ?
 WHERE id = ? AND user_id = ?
```
The `id` and `user_id` are bound from the URL and session respectively — never from the form. The trailing `AND user_id = ?` is a belt-and-braces ownership check: even if a future bug lets a wrong row load, the `UPDATE` itself cannot touch another user's expense. If the row count is 0 after the update (somebody deleted it between the load and the save), treat the request as a 404 — re-rendering with stale data would be confusing.

## Templates
- **Create:** `templates/edit_expense.html` — extends `base.html`, loads `static/css/edit_expense.css` in the `head` block. Layout is structurally identical to `templates/add_expense.html`: a single card-style form with a page title (`Edit expense`), a subtitle (`Update this transaction in your tracker.`), a back link to `/profile`, four fields (amount, category, date, description), a primary submit button (label: `Save changes`), and an error banner slot. Category is a `<select>` with the same fixed option list as the add form, looping over the `categories` context variable, with a disabled default option (`<option value="" disabled selected hidden>`) — but note the loop body uses `{% if form.category == cat %}selected{% endif %}` to pre-select the loaded value, not to re-select after a validation failure's echo. Both code paths use the same `form.category` string, so the conditional works for both. Date defaults to the loaded value (not today), and the `<input type="date" max="{{ today }}">` upper bound stays in place. The amount input reuses the same `step="0.01" min="0.01" max="1000000"` attributes. The description input reuses `maxlength="200"`.
- **Modify:** `templates/profile.html` — no structural changes. (Step 7 already wired the "Add expense" link; this step does not add an "Edit" button on the profile page — that link lives on the future expense detail page, which is out of scope. The edit route is reachable from a `curl`/test or from a future "View expense" page; for now the route just exists and is testable.)

## Files to change
- `app.py`
  - Replace the `edit_expense(id)` stub (currently returns the string `"Edit expense — coming in Step 8"`) with a real view handling both `GET` and `POST`.
  - At the top of the file, add `from flask import abort` to the existing `flask` import line (or extend the import) so the ownership check can call `abort(404)`.
  - On `GET`:
    - If `not session.get("user_id")`, redirect to `url_for("login")`.
    - Open a connection with `get_db()`, run `SELECT id, amount, category, date, description FROM expenses WHERE id = ? AND user_id = ?` with `(id, session["user_id"])`. If the row is `None`, call `abort(404)`.
    - Build a `context` dict mirroring the add-expense shape: `today` (an ISO `YYYY-MM-DD` string for the `<input type="date">` `max` attribute), `categories` (the `EXPENSE_CATEGORIES` tuple, already module-level), `form` (a dict of the loaded values keyed by `amount`, `category`, `date`, `description` — converted to `""` if `description` is `None` so the input renders empty rather than the string `"None"`), `error` (`""` on first render), and `expense_id` (the `id` so the form's `action` URL can be `{{ url_for('edit_expense', id=expense_id) }}`).
    - Render `templates/edit_expense.html` with the context.
  - On `POST`:
    - If `not session.get("user_id")`, redirect to `url_for("login")`.
    - Open a connection with `get_db()`, run the same ownership-check `SELECT`. If the row is `None`, call `abort(404)`. (The row may have been deleted between the GET and the POST; in that case, 404 is correct.)
    - Read `amount`, `category`, `date`, `description` from `request.form`. Strip each.
    - Echo the submitted values back into `context["form"]` (same as Step 7).
    - Run the **same validation sequence as Step 7** in the same order, with the same error messages and the same 400 status. Reuse the constants — do not duplicate the cap or the category list.
    - On any validation failure, re-render the form (including `expense_id`) with a 400 and the appropriate error; do **not** run the `UPDATE`.
    - On success, run a parameterised `UPDATE expenses SET amount = ?, category = ?, date = ?, description = ? WHERE id = ? AND user_id = ?` with `(amount_value, category, parsed_date.isoformat(), description_value, id, session["user_id"])`. Commit, close. Check `cursor.rowcount`: if it's `0`, call `abort(404)` (the row was deleted between the load and the save). Otherwise redirect to `url_for("profile")`.
- (No other file changes in this step.)

## Files to create
- `templates/edit_expense.html` — see Templates above. The form's `action` is `{{ url_for('edit_expense', id=expense_id) }}` so a future refactor that changes the URL pattern doesn't break the form. The submit button's text is `Save changes` (not `Add expense`). The back link points to `{{ url_for('profile') }}` with the same `&larr; Back to dashboard` copy.
- `static/css/edit_expense.css` — per-page override loaded after `style.css` via `{% block head %}`, matching the convention from `add_expense.css`. The rule set is **structurally identical** to `add_expense.css` — the form layout, field rows, error banner, and back link are the same. The only allowed difference is the class names: prefix everything with `edit-expense-` instead of `add-expense-` (so `.edit-expense-section`, `.edit-expense-container`, `.edit-expense-header`, `.edit-expense-title`, `.edit-expense-subtitle`, `.edit-expense-card`, `.edit-expense-error`, `.edit-expense-optional`, `.edit-expense-back`). Reuse `--accent`, `--max-width`, the existing button classes (`.btn-submit` from `add_expense.css` if it is generic enough, otherwise define `.edit-expense-submit` to match), and the form-input baseline from `style.css`. **No new hex values** — every colour, font, and spacing token references an existing `var(--…)` in `style.css`.

  If `add_expense.css`'s button rule (`.btn-submit`) is a generic button style and not coupled to the add form, reuse it directly and skip defining a separate `.edit-expense-submit`. Otherwise add an equivalent rule to `edit_expense.css` with the same visuals.

## New dependencies
No new dependencies. The route uses only `sqlite3` (already imported in `app.py`), stdlib `datetime.date` (already imported), and `flask.abort` (one new symbol from the already-imported `flask` package).

## Rules for implementation
- No SQLAlchemy or ORMs — raw `sqlite3` via `database.db.get_db()`.
- Parameterised queries only — both the ownership-check `SELECT` and the `UPDATE` use `?` placeholders for every value. `id` is bound from the URL, `user_id` from `session`, never from the form.
- Passwords hashed with werkzeug — N/A for this step, no passwords involved. (Kept here for parity with the global Rules in other specs.)
- Use CSS variables — never hardcode hex values in `edit_expense.css` or `edit_expense.html`. All colours, fonts, radii, and spacing come from `style.css`'s `:root` tokens.
- All templates extend `base.html` — `edit_expense.html` does so via `{% extends "base.html" %}`.
- The `EXPENSE_CATEGORIES` tuple is reused from Step 7 — do not redefine it. The edit form loops over the same list and renders the same `<option>` markup.
- Validation (must match Step 7 exactly — same order, same error messages, same 400 status):
  1. **Amount** — must parse as a positive float. Reject empty, non-numeric, zero, and negative. Two-decimal-place precision is fine (e.g. `12.50`); no scientific notation, no commas, no currency symbol. Cap: `1_000_000.00` — anything above that is rejected as a sanity cap.
  2. **Category** — must be present in `EXPENSE_CATEGORIES`. Reject anything else.
  3. **Date** — must be a valid `YYYY-MM-DD` (use `date.fromisoformat`; any `ValueError` / `TypeError` means invalid). Must be `<= today` — future-dated expenses are not allowed.
  4. **Description** — optional. After `.strip()`, if the result is empty, store `NULL`; otherwise store the stripped string. Max length 200 characters.
  5. Submitting with a missing `user_id` in the session is treated as "not logged in" → 302 to `/login`. The login redirect happens before any form processing.
- Error messages are short, human, and lower-case to match the existing register/login/add-expense error copy.
- The `description` field, when present, is stored as a plain string. No HTML, no markdown, no link parsing. The template renders it with `{{ form.description }}` (Jinja auto-escapes), so XSS is not a concern.
- The form has no JS. Plain submit, server-side redirect. Do not introduce client-side validation that diverges from the server-side rules.
- Ownership enforcement is non-negotiable:
  - GET: ownership-checked `SELECT`; `abort(404)` on miss.
  - POST: ownership-checked `SELECT` on entry; `abort(404)` on miss. `UPDATE` carries `AND user_id = ?` in the `WHERE` clause as a second line of defence. `cursor.rowcount == 0` after the `UPDATE` (concurrent delete) → `abort(404)`.
  - 404 is the right response — 403 would leak the existence of an expense the user can't see, and a 302 to `/profile` would be confusing.
- The success path is a 302 to `/profile` (no filter args), so the edited row appears in the default "All time" view.
- Do not touch the seeded demo data, `database/db.py`, or any other route's behaviour.
- Do not add a flash-message framework. Step 8 ships without flash messages; if a future step wants a "Expense updated" toast, it can add one globally.
- The edit template's form `action` is `{{ url_for('edit_expense', id=expense_id) }}` — never hardcode `/expenses/{{ expense_id }}/edit`.

## Definition of done
- Visiting `/expenses/<id>/edit` while logged out redirects to `/login`.
- Visiting `/expenses/<id>/edit` while logged in, with `<id>` belonging to the logged-in user, renders a form pre-filled with that expense's amount, category, date, and description, a primary `Save changes` submit button, and a back link to `/profile`. The category `<select>` has the matching option pre-selected; the date input shows the loaded date; the description input shows the loaded description (empty if the row's description is `NULL`).
- Visiting `/expenses/<id>/edit` while logged in, with `<id>` belonging to **a different user**, returns a 404 (no form rendered, no row data leaked in the response body).
- Visiting `/expenses/<id>/edit` with a non-existent `<id>` returns a 404.
- Submitting a valid form updates the matching row in `expenses` with the new amount, category, date, and description. The response is a 302 to `/profile`. `user_id`, `id`, and `created_at` are unchanged.
- After the redirect, the edited row appears in the recent-transactions table on `/profile` with the new values; the summary stats and category breakdown reflect the new amount.
- Submitting with `amount` empty / non-numeric / zero / negative / above the sanity cap re-renders the form with a 400 and the appropriate error message; no `UPDATE` runs; the row is unchanged.
- Submitting with `category` empty or not in `EXPENSE_CATEGORIES` re-renders with a 400 and the appropriate error; no `UPDATE` runs.
- Submitting with `date` empty / malformed / in the future re-renders with a 400 and the appropriate error; no `UPDATE` runs.
- Submitting with `description` empty / whitespace-only stores `NULL` in the `description` column (verified by inspecting the row); submitting with a 200+ character description re-renders with a 400 and an error; submitting with a normal description stores the trimmed string.
- A `POST /expenses/<id>/edit` from a logged-in user for an `<id>` belonging to a different user returns a 404; no row is updated.
- The submitted (invalid) values are echoed back into the form fields after a validation failure, with the category re-selected and the date / description / amount re-populated. The user does not have to re-type everything.
- The `UPDATE` uses `?` placeholders for all six bound values; the `WHERE` clause includes `id = ? AND user_id = ?`. No string interpolation appears in the SQL.
- The form is keyboard-navigable: tabbing reaches amount, category, date, description, submit, back link, in that order. Each field has an associated `<label>`.
- The app still starts on port 5001 with `python app.py`. Register/login/logout/profile/add-expense still work; the seed data still loads; the `/expenses/<id>/delete` stub still returns its placeholder string.
- No new dependencies were added to `requirements.txt` (or wherever deps live in this repo).
- Running `python -c "from app import app; c = app.test_client()"` plus a `GET /expenses/<id>/edit` and a `POST /expenses/<id>/edit` with a logged-in session returns 200 / 302 / 400 / 404 in the expected cases (covered in detail in the items above).
