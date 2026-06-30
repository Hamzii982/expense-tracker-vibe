# Spec: Delete Expense

## Overview
This step turns the `/expenses/<id>/delete` stub into a working delete-expense flow, the third and final CRUD step after Step 7 (add) and Step 8 (edit). A logged-in user visits a confirmation page for one of their own expenses, sees the expense's details alongside a "Delete" button, confirms, and the row is removed from `expenses`. The user is then redirected back to `/profile` where the row no longer appears and the summary stats and category breakdown reflect the new totals. The route is ownership-checked: if the expense belongs to a different user, the request 404s — students can't peek at or delete other people's data. There is no soft-delete, no undo, and no flash message; a successful delete is communicated by the row simply being gone on `/profile`.

## Depends on
- Step 1 — Database setup. The `expenses` table exists with columns `id, user_id, amount, category, date, description, created_at`.
- Step 2 — Registration. `session["user_id"]` is set on successful registration.
- Step 3 — Login and Logout. `session["user_id"]` is set on successful login.
- Step 5 — Backend Routes for Profile Page. `/profile` reads from `expenses`; a deleted row will simply disappear from the recent-transactions table, summary stats, and category breakdown without further changes.
- Step 6 — Date Filter. The `/profile` route supports date filtering. Deleting a row whose date is outside the active filter is a no-op from the UI's perspective — that's fine, the row is gone either way.
- Step 7 — Add Expense. The `EXPENSE_CATEGORIES` tuple and the add-expense template already exist; the delete confirmation page mirrors the add/edit templates' layout.
- Step 8 — Edit Expense. The `edit_expense(id)` view established the ownership-checked `SELECT` pattern (`WHERE id = ? AND user_id = ?`) and the `cursor.rowcount == 0` → 404 belt-and-braces guard. This step reuses both. The confirmation template mirrors the add/edit template layout.

## Routes
- `GET /expenses/<id>/delete` — load the expense (ownership-checked against `session["user_id"]`), render a confirmation page showing the expense's details — logged-in only
- `POST /expenses/<id>/delete` — delete the row (ownership-checked), redirect to `/profile` — logged-in only

Both verbs handled by the same `delete_expense(id)` view. The GET response is `200` with `templates/delete_expense.html`. The POST success path is a `302` to `url_for("profile")`. Both verbs require a logged-in session; an unauthenticated request is a `302` to `/login` before any processing happens.

If the `id` in the URL doesn't exist, **or** belongs to a different user, the route returns `404` (renders `templates/404.html` if present, otherwise the Flask default 404 page). This is ownership enforcement, not a UX nicety — a user must not be able to view the delete confirmation for someone else's expense, and a user must not be able to delete it via `POST` either. The check is the same single query on both verbs: `SELECT id FROM expenses WHERE id = ? AND user_id = ?`. If that returns no row, return `abort(404)`.

The route does **not** accept an `id` of zero or negative — `<int:id>` in the URL converter already filters those out, returning a Flask 404 routing error. No additional check needed.

The route does **not** preserve the date filter from `/profile` in the redirect — Step 7 and Step 8 established that add/edit go to `All time` on success, and this step follows the same pattern.

## Database changes
No database changes. The `expenses` table from Step 1 has the right shape. The delete is a hard `DELETE` — there is no soft-delete column, no `deleted_at`, no archive table. A successful delete removes exactly one row from `expenses`; there are no child rows to cascade to.

The exact delete statement:
```sql
DELETE FROM expenses
 WHERE id = ? AND user_id = ?
```
The `id` is bound from the URL, `user_id` from `session` — never from the form. The trailing `AND user_id = ?` is a belt-and-braces ownership check: even if a future bug lets a wrong row load, the `DELETE` itself cannot touch another user's expense. If the row count is 0 after the delete (the row was already deleted between the load and the delete), treat the request as a 404 — re-rendering the confirmation page for a row that no longer exists would be confusing.

## Templates
- **Create:** `templates/delete_expense.html` — extends `base.html`, loads `static/css/delete_expense.css` in the `head` block. Layout is structurally similar to `templates/edit_expense.html`: a single card-style page with a page title (`Delete expense`), a subtitle (`This action cannot be undone.`), a back link to `/profile`, a "details" block showing the expense's amount, category, date, and description (so the user can confirm they're deleting the right row), and a confirmation form with two buttons: a primary destructive `Delete expense` submit button and a secondary `Cancel` link back to `/profile`. The form's `action` is `{{ url_for('delete_expense', id=expense_id) }}` and uses `method="post"` so the destructive action can't be triggered by a prefetch or a GET-only crawler. The `Cancel` link is a plain `<a class="btn-ghost" href="{{ url_for('profile') }}">`, not a submit button — clicking it abandons the delete without any state change.
- **Modify:** `templates/profile.html` — no structural changes in this step. The "Edit" / "Delete" controls for each row are out of scope for this step; the delete route is reachable from a `curl`/test or from a future expense detail page. (Step 8 made the same call for "Edit" — this step mirrors it for "Delete".)

## Files to change
- `app.py`
  - Replace the `delete_expense(id)` stub (currently returns the string `"Delete expense — coming in Step 9"`) with a real view handling both `GET` and `POST`. The existing stub is decorated with `@app.route("/expenses/<int:id>/delete")` only — change it to accept `methods=["GET", "POST"]`.
  - `from flask import abort` is already imported (Step 8 added it), so no change to the imports block.
  - On `GET`:
    - If `not session.get("user_id")`, redirect to `url_for("login")`.
    - Open a connection with `get_db()`, run `SELECT id, amount, category, date, description FROM expenses WHERE id = ? AND user_id = ?` with `(id, session["user_id"])`. If the row is `None`, call `abort(404)`.
    - Build a `context` dict containing `expense_id` (the `id`, for the form's `action` URL), and an `expense` dict with `amount`, `category`, `date`, `description` from the loaded row (convert `None` description to `""` so the template renders an em-dash or "—" instead of the literal string `"None"`).
    - Render `templates/delete_expense.html` with the context.
  - On `POST`:
    - If `not session.get("user_id")`, redirect to `url_for("login")`.
    - Open a connection with `get_db()`, run the ownership-check `SELECT` (same query as GET). If the row is `None`, call `abort(404)`. (The row may have been deleted between the GET and the POST; in that case, 404 is correct.)
    - Run a parameterised `DELETE FROM expenses WHERE id = ? AND user_id = ?` with `(id, session["user_id"])`. Commit, close.
    - Check `cursor.rowcount`: if it's `0`, call `abort(404)` (the row was already deleted between the load and the delete). Otherwise redirect to `url_for("profile")`.
- (No other file changes in this step.)

## Files to create
- `templates/delete_expense.html` — see Templates above. The form's `action` is `{{ url_for('delete_expense', id=expense_id) }}` so a future refactor that changes the URL pattern doesn't break the form. The submit button's text is `Delete expense`. The cancel link points to `{{ url_for('profile') }}` with the same `&larr; Cancel and go back` copy.
- `static/css/delete_expense.css` — per-page override loaded after `style.css` via `{% block head %}`, matching the convention from `add_expense.css` and `edit_expense.css`. The layout (section / container / header / card / back link) is structurally identical to `add_expense.css` and `edit_expense.css` — the form layout, field rows, and back link follow the same pattern. The only allowed differences are: (a) the class names are prefixed with `delete-expense-` instead of `add-expense-` or `edit-expense-` (so `.delete-expense-section`, `.delete-expense-container`, `.delete-expense-header`, `.delete-expense-title`, `.delete-expense-subtitle`, `.delete-expense-card`, `.delete-expense-details`, `.delete-expense-detail-row`, `.delete-expense-actions`, `.delete-expense-back`), and (b) the primary submit button uses a destructive colour (the existing `--danger` token from `style.css`, or a red-equivalent already defined in `style.css` — verify before adding a new token). The `Cancel` link reuses `.btn-ghost` from `style.css`. Reuse `--accent`, `--max-width`, the existing button classes, and the form-input baseline from `style.css`. **No new hex values** — every colour, font, and spacing token references an existing `var(--…)` in `style.css`.

## New dependencies
No new dependencies. The route uses only `sqlite3` (already imported in `app.py`) and `flask.abort` (already imported since Step 8).

## Rules for implementation
- No SQLAlchemy or ORMs — raw `sqlite3` via `database.db.get_db()`.
- Parameterised queries only — both the ownership-check `SELECT` and the `DELETE` use `?` placeholders for every value. `id` is bound from the URL, `user_id` from `session`, never from the form.
- Passwords hashed with werkzeug — N/A for this step, no passwords involved. (Kept here for parity with the global Rules in other specs.)
- Use CSS variables — never hardcode hex values in `delete_expense.css` or `delete_expense.html`. All colours, fonts, radii, and spacing come from `style.css`'s `:root` tokens. If no destructive-colour token exists in `style.css`, add one (e.g. `--danger`) to `:root` rather than hardcoding a hex in `delete_expense.css`.
- All templates extend `base.html` — `delete_expense.html` does so via `{% extends "base.html" %}`.
- The destructive submit button is rendered as `<button type="submit" class="btn-danger">Delete expense</button>` (or equivalent class name) styled with the destructive token. The form uses `method="post"` so a prefetch, link preview, or crawler can't trigger the delete with a GET.
- The `Cancel` link is a plain `<a>`, not a submit button — clicking it abandons the confirmation without any state change. The user lands back on `/profile` and the row is still there.
- The confirmation page shows the expense's amount, category, date, and description so the user can verify they're deleting the right row. Amount is formatted with two decimal places (e.g. `12.50`), date is rendered as the stored ISO string or a short human form (e.g. `Jun 2, 2026` — match the format Step 8 uses in the edit form's date field), and description is shown as `—` when the row's description is `NULL`.
- Error messages are not needed on this step — the only failure modes are ownership / not-found (404) and not-logged-in (302 to `/login`), and the template doesn't display a validation error banner. The `404.html` template (if it exists) handles the ownership case.
- The form has no JS. Plain submit, server-side redirect. Do not introduce client-side "Are you sure?" dialogs — the dedicated confirmation page already plays that role, and stacking two confirmations would be annoying.
- Ownership enforcement is non-negotiable:
  - GET: ownership-checked `SELECT`; `abort(404)` on miss.
  - POST: ownership-checked `SELECT` on entry; `abort(404)` on miss. `DELETE` carries `AND user_id = ?` in the `WHERE` clause as a second line of defence. `cursor.rowcount == 0` after the `DELETE` (concurrent delete, or the row was already gone between load and delete) → `abort(404)`.
  - 404 is the right response — 403 would leak the existence of an expense the user can't see, and a 302 to `/profile` would be confusing.
- The success path is a 302 to `/profile` (no filter args), so the deleted row disappears from the default "All time" view.
- Do not touch the seeded demo data, `database/db.py`, or any other route's behaviour.
- Do not add a flash-message framework. Step 9 ships without flash messages; if a future step wants a "Expense deleted" toast, it can add one globally.
- Do not add a soft-delete column or a `deleted_at` timestamp — out of scope. A hard `DELETE` is what this step ships.
- The delete template's form `action` is `{{ url_for('delete_expense', id=expense_id) }}` — never hardcode `/expenses/{{ expense_id }}/delete`.

## Definition of done
- Visiting `/expenses/<id>/delete` while logged out redirects to `/login`.
- Visiting `/expenses/<id>/delete` while logged in, with `<id>` belonging to the logged-in user, renders a confirmation page showing the expense's amount, category, date, and description, a primary destructive `Delete expense` submit button, and a secondary `Cancel` link to `/profile`. The form's `method` is `post` and `action` points to the same URL.
- Visiting `/expenses/<id>/delete` while logged in, with `<id>` belonging to **a different user**, returns a 404 (no confirmation page rendered, no row data leaked in the response body).
- Visiting `/expenses/<id>/delete` with a non-existent `<id>` returns a 404.
- `POST`ing to `/expenses/<id>/delete` with a logged-in session and `<id>` belonging to that user deletes the row from `expenses`. The response is a 302 to `/profile`. After the redirect, the row no longer appears in the recent-transactions table, summary stats, or category breakdown on `/profile`.
- `POST`ing to `/expenses/<id>/delete` from a logged-in user for an `<id>` belonging to a different user returns a 404; no row is deleted.
- `POST`ing to `/expenses/<id>/delete` for a non-existent `<id>` returns a 404; no row is deleted.
- Clicking the `Cancel` link on the confirmation page navigates to `/profile` without making any database changes — verified by loading the confirmation page, clicking Cancel, and confirming the row is still there.
- The `DELETE` uses `?` placeholders for both bound values; the `WHERE` clause includes `id = ? AND user_id = ?`. No string interpolation appears in the SQL.
- The confirmation page is keyboard-navigable: tabbing reaches the destructive submit button, the cancel link, and the back link in a sensible order. The destructive submit button has a clear accessible label (`Delete expense`).
- The app still starts on port 5001 with `python app.py`. Register/login/logout/profile/add-expense/edit-expense still work; the seed data still loads; the `404` behaviour for unknown routes still works.
- No new dependencies were added to `requirements.txt` (or wherever deps live in this repo).
- Running `python -c "from app import app; c = app.test_client()"` plus a `GET /expenses/<id>/delete` and a `POST /expenses/<id>/delete` with a logged-in session returns 200 / 302 / 404 in the expected cases (covered in detail in the items above).