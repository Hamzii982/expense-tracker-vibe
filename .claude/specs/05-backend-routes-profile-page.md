# Spec: Backend Routes for Profile Page

## Overview
This step replaces the hardcoded demo data inside the `/profile` view with real database queries against the `users` and `expenses` tables. The UI built in Step 4 already expects four pieces of context — `user`, `stats`, `transactions`, `category_breakdown` (plus `category_max`) — so this step is purely a backend wiring exercise: fetch the logged-in user's record, compute aggregate stats, pull the most recent transactions, and group spending by category. After this lands, `/profile` reflects whatever expenses exist for the signed-in user, and Step 7 (`/expenses/add`) can begin populating real data without further profile work.

## Depends on
- Step 1 — Database setup. Both `users` (`id`, `name`, `email`, `created_at`) and `expenses` (`id`, `user_id`, `amount`, `category`, `date`, `description`, `created_at`) tables must exist.
- Step 2 — Registration. The `session["user_id"]` key must be set on signup so a freshly registered user lands on a populated `/profile`.
- Step 3 — Login and Logout. Session plumbing must be reliable; `/profile` must redirect to `/login` when the session is empty.
- Step 4 — Profile Page Design. The template `templates/profile.html` and its `profile.css` are already in place and define the exact context variables this step must produce.

## Routes
- `GET /profile` — render the profile page using real DB data for the logged-in user — logged-in only (redirect to `/login` if not authenticated)

No other routes change. `/logout`, `/expenses/add`, `/expenses/<id>/edit`, `/expenses/<id>/delete` are out of scope.

## Database changes
No database changes. The `users` and `expenses` tables from Step 1 already cover everything this step needs. All reads go through `database/db.py:get_db()`.

## Templates
- **Modify:** `templates/profile.html` — no structural changes. The template already references `user.{name,email,initials,joined}`, `stats.{total_spent,txn_count,top_category,avg_monthly}`, `transactions[]`, `category_breakdown[]`, and `category_max`. The view just needs to pass those names.

No new templates. No CSS changes (`profile.css` already styles every section the template renders).

## Files to change
- `app.py`
  - Replace the hardcoded `user`, `stats`, `transactions`, `category_breakdown` literals inside `profile()` with computed values from the database.
  - Look up the current user by `session["user_id"]` and build the `user` dict (`name`, `email`, `initials`, `joined` — `joined` formatted as the month-and-year string e.g. `"May 2026"`).
  - Compute `stats` from a single aggregate query against `expenses` for the current user:
    - `total_spent` — `SUM(amount)`
    - `txn_count` — `COUNT(*)`
    - `top_category` — category with the highest `SUM(amount)`; `None` if no expenses yet (render as `"—"` in the template is fine, or pass the literal `"—"` from the view)
    - `avg_monthly` — `total_spent` divided by the number of distinct calendar months that contain at least one expense (rounded to 2 dp); `0.00` if no expenses
  - Fetch `transactions` as the **8 most recent** rows for the user, ordered by `date DESC, id DESC` (id as the tiebreaker for same-day entries), projecting to `{date, description, category, amount}` so the template needs no changes.
  - Compute `category_breakdown` as one row per category present in the user's expenses: `{name, total}` where `total = SUM(amount)` per category, ordered by `total DESC`. Also compute `category_max` for the bar-width `var(--pct)` calculation. If the user has zero expenses, pass `category_breakdown=[]` and `category_max=0` (the template's `{% for %}` and the `max()` call must each handle an empty list — see Rules).
  - Open and close the connection per request via `with get_db() as conn:` is acceptable, but the existing code in `app.py` uses `conn = get_db(); … conn.close()`. Match that style for consistency.
  - Keep the existing authentication guard at the top of the view (`if not session.get("user_id"): return redirect(url_for("login"))`).

## Files to create
None.

## New dependencies
No new dependencies. Everything (`sqlite3`, `flask`, `werkzeug`) is already installed.

## Rules for implementation
- No SQLAlchemy or ORMs. Use raw `sqlite3` via `database.db.get_db()`.
- Parameterised queries only. Every `?` placeholder is non-negotiable, including the dynamic `LIMIT ?` for the recent-transactions query and the category-grouping query.
- Use `werkzeug` for any password handling that creeps in (it won't in this step — the route never touches `password_hash`).
- Use CSS variables — never hardcode hex values. The template is already correct here; do not add inline styles or new colour literals to `profile.html` while editing the route.
- All templates extend `base.html` (no change in this step, but noted for the spec record).
- The "joined" string is derived from `users.created_at` (a `datetime('now')` text value in `YYYY-MM-DD HH:MM:SS` form). Parse just enough of it to render `"May 2026"` — a small slice on `created_at[:7]` plus a month-name lookup, or `datetime.strptime` if available. Do not pull in `python-dateutil` or any new parser.
- Initials must be derived from the user's `name` field. Take the first letter of the first two whitespace-separated words, uppercased — e.g. `"Demo User"` → `"DU"`, `"Alice"` → `"A"`. Handle empty/whitespace names defensively (fall back to `"?"`).
- "Top category" handling: when there are zero expenses, pass `"—"` (em-dash) for `top_category` so the UI doesn't render an empty stat. Same approach for `avg_monthly` → `0.00`.
- "Avg / month" must use the **distinct calendar months that contain at least one expense**, not `COUNT(*) / N` over some assumed window. A new user with two expenses in the same month has `avg_monthly = total_spent / 1` (rounded to 2 dp); two expenses in different months has `avg_monthly = total_spent / 2`.
- `category_breakdown` must include a row for every category the user has spent in, not just the fixed seven. If the user adds an "Other" expense in Step 7, that's the row that shows up — don't filter to a hardcoded list.
- `category_max` must be `0` when `category_breakdown` is empty so the template's `cat.total / category_max` does not divide by zero. Easiest is to set `category_max = max((c["total"] for c in category_breakdown), default=0)` in the view.
- Transaction ordering is `date DESC, id DESC`. The seed inserts same-day rows (e.g. two on `2026-06-04`), so the `id` tiebreaker keeps the order stable across renders.
- The recent-transactions `LIMIT` value (8) is hardcoded for now. It mirrors the Step 4 demo; promoting it to a per-page constant is a Step 7+ concern.
- Keep the view pure — no `flash()`, no new session keys, no helper modules. This step only reads.

## Definition of done
- Visiting `/profile` without being logged in redirects to `/login`.
- Visiting `/profile` while logged in as the seeded `demo@spendly.com` user returns HTTP 200 and renders the eight seeded expenses in the recent-transactions table.
- The "Total spent" stat equals the sum of the eight seeded amounts (rounded to 2 dp in the template).
- The "Transactions" stat equals `8`.
- The "Top category" stat equals `"Bills"` (the seeded `120.00` Electricity row is the largest single-category total).
- The "Avg / month" stat reflects `total_spent` divided by the number of distinct months represented by the seeded data (all rows fall in June 2026, so the divisor is 1 and `avg_monthly == total_spent`).
- `category_breakdown` contains exactly seven rows for the demo user (Food, Transport, Bills, Health, Entertainment, Shopping, Other) in descending order of `total`.
- `category_max` equals the largest single-category total (120.00) for the demo user.
- Logging in as a freshly registered user with zero expenses renders the profile with `txn_count == 0`, `total_spent == $0.00`, `top_category == "—"`, an empty recent-transactions table, and an empty `category_breakdown` — and does **not** raise (no division by zero, no `max()` on an empty iterable).
- The "Member since" string on a freshly registered user reflects the current month and year (e.g. `"June 2026"`).
- Initials for `Demo User` render as `DU`; initials for a single-word name render as the first letter uppercased.
- No `SELECT` uses string interpolation — every query has `?` placeholders.
- The app still starts on port 5001 with `python app.py`. Existing register/login/logout flows remain unchanged.