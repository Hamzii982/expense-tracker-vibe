# Spec: Date Filter for Profile Page

## Overview
The profile page currently shows the user's all-time spending stats, recent transactions, and category breakdown. This step adds a date-range filter so the user can narrow the view to a specific month or a custom date range. The filter applies to all four data sections on the page (summary stats, recent transactions, category breakdown) so the user gets a consistent view of spending within the chosen window. The filter is a GET form (so the URL is shareable and refreshable) and persists across renders via query-string parameters.

## Depends on
- Step 1 — Database setup. `expenses.date` column must exist (it does, stored as `YYYY-MM-DD`).
- Step 4 — Profile Page Design. `templates/profile.html` and `static/css/profile.css` exist.
- Step 5 — Backend Routes for Profile Page. The four helpers (`_get_user`, `_get_stats`, `_get_recent_transactions`, `_get_category_breakdown`) are in place; this step threads a date range through them.

## Routes
- `GET /profile` — render the profile page, optionally filtered by date range — logged-in only (redirect to `/login` if not authenticated)

The single route accepts these query-string parameters (all optional):
- `period` — preset shortcut: `all` (default), `this_month`, `last_month`, `last_3_months`, `last_6_months`, `this_year`
- `from` — explicit start date in `YYYY-MM-DD` form (overrides `period` when present)
- `to` — explicit end date in `YYYY-MM-DD` form (overrides `period` when present)

If both `from` and `to` are present, that range wins over `period`. If only one is present, the other defaults to "all-time on that side" (i.e. only `from` set means from that date forward; only `to` set means up to that date).

No new routes are added. The single `/profile` endpoint grows query-string support.

## Database changes
No database changes. All filtering happens via `WHERE date >= ?` / `WHERE date <= ?` clauses on the existing `expenses.date` column. The column stores ISO `YYYY-MM-DD` strings, so string comparison sorts and filters correctly.

## Templates
- **Modify:** `templates/profile.html`
  - Add a date-filter bar above the summary stats row. Contains:
    - A `<form method="get" action="/profile">` with six preset period buttons (`All time`, `This month`, `Last month`, `Last 3 months`, `Last 6 months`, `This year`) — clicking submits the form with `?period=<key>`.
    - Two `<input type="date">` fields (`from`, `to`) that submit on change via a small inline `onsubmit` (or via a "Apply" submit button — see Rules).
    - An active-filter summary line showing the currently applied range (e.g. `"Showing: June 2026"` or `"Showing: 2026-01-01 → 2026-06-22"`).
  - Pass the active filter (`filter_label`, `active_period`, `filter_from`, `filter_to`) from the view to the template so the form can mark the active preset as pressed/highlighted and echo the custom range back into the inputs.
  - No structural changes to the four existing sections — they keep their current shape but now read filtered data.

- **Modify:** `static/css/profile.css`
  - Add styles for the new filter bar (a horizontal row of period buttons + two date inputs). Match the existing pill / `--accent` aesthetic. Active preset button uses the same filled state as `.btn-primary`; inactive uses `.btn-ghost`. No new hex values.

## Files to change
- `app.py`
  - Update `profile()` to:
    - Read `request.args.get("period")`, `request.args.get("from")`, `request.args.get("to")`.
    - Validate `period` against the allowed set; anything unknown falls back to `"all"`.
    - Validate `from` and `to` are either empty or parseable as `YYYY-MM-DD`; on parse failure, ignore the bad value and behave as if unset.
    - Resolve the final date range:
      - `all` → no `date` filter applied
      - `this_month` → `from = first-of-current-month`, `to = today`
      - `last_month` → `from = first-of-last-month`, `to = last-day-of-last-month`
      - `last_3_months` → `from = first-of-(today minus 3 months + 1 day)`, `to = today`
      - `last_6_months` → same as above with 6
      - `this_year` → `from = YYYY-01-01 (current year)`, `to = today`
      - explicit `from` / `to` → use as-is
    - Compute a `filter_label` string for the UI summary (e.g. `"All time"`, `"June 2026"`, `"Jan 1 – Jun 22, 2026"`).
  - Update the four helpers to accept an optional `date_from` / `date_to` argument (or a single `where_sql` + params tuple — see Rules for chosen style) and append the right `WHERE date >= ? AND date <= ?` clauses to every existing query.
  - Pass `filter_label`, `active_period`, `filter_from`, `filter_to` into the template context alongside the existing `user`, `stats`, `transactions`, `category_breakdown`, `category_max`.

- `templates/profile.html` — see Templates above.
- `static/css/profile.css` — see Templates above.

## Files to create
None.

## New dependencies
No new dependencies. Date math uses only `datetime.date` (already imported as `datetime` at the top of `app.py`) — no need for `python-dateutil` or similar.

## Rules for implementation
- No SQLAlchemy or ORMs — raw `sqlite3` via `database.db.get_db()`.
- Parameterised queries only — the new `WHERE date >= ?` and `WHERE date <= ?` clauses must use `?` placeholders. The dynamic `LIMIT ?` for the recent-transactions query stays parameterised.
- Use CSS variables — never hardcode hex values in `profile.css` or `profile.html`.
- All templates extend `base.html` (no change here, but noted).
- Date math uses the stdlib `datetime` module only. Use `date.today()`, `date.replace(day=1)`, and `(d.replace(day=1) - timedelta(days=1))` style idioms — do not pull in `python-dateutil` or `calendar.monthrange` workarounds.
- "Last 3 months" / "Last 6 months" definitions: count back from the start of the current month. `last_3_months` covers the current month plus the two previous full calendar months (e.g. on June 22, 2026 → April 1 → June 22). The exact boundary is `first_of_current_month - timedelta(days=1) → first_of_(that month - 1 month)`; iterate or use a small loop — keep it readable, no clever one-liners.
- Empty / missing query params are equivalent to "all time" — no error, just no filter.
- Custom range validation: if `from` is later than `to`, treat it as an empty result (still render the page, but with zero stats/transactions/categories) and pass a `filter_label` like `"No results"` — do not 400.
- Helpers take the date range as **keyword args** (`date_from=None`, `date_to=None`) and build the SQL conditionally so the "all time" path stays identical to today's behaviour. Don't add a new `where_sql` string parameter — that's a SQL-injection-shaped footgun for future maintainers.
- The filter is a GET form. The active filter is rendered in the form so refreshing the page preserves it. The "All time" preset is just a link/button to `/profile` with no query string.
- The active period button gets a `aria-pressed="true"` attribute and the filled `.btn-primary` style; the rest get `.btn-ghost` and `aria-pressed="false"`.
- Custom range submit: a "Apply" button is fine (simpler than `onchange` JS). Do not introduce a JS file just for this — inline a one-line `onsubmit` only if needed to clear stale params.
- The active-filter summary line appears above the stats row and is small / muted, not a callout. It should be a single sentence ("Showing: <label>") — not a card.
- Recent transactions within a filtered range must still cap at 8 rows (existing `LIMIT 8` behaviour). Filtering happens in `WHERE`, not in Python.
- Stats within a filtered range: `total_spent`, `txn_count`, `top_category`, `avg_monthly` all reflect the filtered subset. `month_count` (and therefore `avg_monthly`) uses the distinct months present *within the filter*, not the all-time number.
- Category breakdown within a filtered range: only categories with spending in the filter window appear; `category_max` is recomputed for the filtered set.
- Do not touch the seeded demo data or `database/db.py`.

## Definition of done
- Visiting `/profile` with no query string still returns the all-time view (no regression on the Step 5 behaviour).
- Visiting `/profile?period=this_month` returns a page filtered to the current calendar month. The "This month" preset button is visually highlighted.
- Visiting `/profile?period=last_month` returns a page filtered to the previous calendar month (verified by checking a known seeded date, e.g. all 8 seeded expenses in `2026-06` are filtered out when viewed in `June 2026` with `period=last_month`).
- Visiting `/profile?period=last_3_months` and `?period=last_6_months` and `?period=this_year` each return the correct window, with the matching preset button highlighted.
- Visiting `/profile?from=2026-06-01&to=2026-06-15` returns only expenses whose `date` falls on or between those bounds.
- Visiting `/profile?from=2026-06-01` (no `to`) returns expenses from that date forward.
- Visiting `/profile?to=2026-06-15` (no `from`) returns expenses up to that date.
- Visiting `/profile?from=2026-12-01&to=2026-01-01` (inverted range) returns an empty results page with a `"No results"` label and does not raise.
- Visiting `/profile?period=garbage` falls back to "all time" silently (no 400).
- Visiting `/profile?from=not-a-date` falls back to "all time" silently.
- The active-filter summary line reads `"Showing: <label>"` matching whichever range is active.
- All four data sections (stats, recent transactions, category breakdown) update consistently for the active filter — selecting `this_month` changes the total, the transaction list, the categories, and the bar widths together.
- `category_max` is recomputed per filter; with an empty filtered set it's `0` (no division by zero).
- `top_category` is `"—"` when the filtered range has zero expenses.
- `avg_monthly` is `0.00` when the filtered range has zero months with expenses.
- The "View all" link in the recent-transactions card stays a non-functional `<span>` for now (still out of scope).
- The filter form is keyboard-navigable: tabbing through the period buttons and date inputs reaches every control in a sensible order.
- No `SELECT` uses string interpolation; the new `WHERE date >= ?` / `WHERE date <= ?` clauses use `?` placeholders.
- The app still starts on port 5001 with `python app.py`. Register/login/logout still work; the seed data still loads.
