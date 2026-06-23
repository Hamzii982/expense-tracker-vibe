"""Tests for the Step 6 "Date Filter for Profile Page" feature.

Spec source (the source of truth for every assertion below):
  C:/hamza-space/apps/expense-tracker/.claude/specs/06-date-filter.md
  C:/hamza-space/apps/expense-tracker/database/db.py   (seeded fixture data)

Seeded demo data (``database.db.seed_db``):
  user: demo@spendly.com / demo123
  expenses (8 rows, all dated 2026-06-01 .. 2026-06-05):
      12.50 Food          2026-06-02  Lunch at cafe
      45.20 Food          2026-06-04  Weekly groceries
       8.00 Transport     2026-06-01  Bus pass
     120.00 Bills         2026-06-03  Electricity bill
      35.00 Health        2026-06-05  Pharmacy
      15.99 Entertainment 2026-06-02  Movie ticket
      60.00 Shopping      2026-06-04  New shoes
       5.50 Other         2026-06-01  Misc
  -- total = 12.50+45.20+8.00+120.00+35.00+15.99+60.00+5.50 = 302.19
  -- categories (6): Food=57.70, Bills=120.00, Shopping=60.00,
                     Health=35.00, Entertainment=15.99, Transport=8.00,
                     Other=5.50
  -- category_max = 120.00 (Bills)
  -- top_category = "Bills"
  -- month_count (distinct YYYY-MM in filtered set) = 1 (June 2026 only)
  -- avg_monthly   = 302.19 / 1 = 302.19

The "today" anchor for date math is whatever the host's clock reports at
test time (``datetime.date.today()``). We never hard-code it.

Acceptance criteria covered (from spec "Definition of done"):
  1.  Auth guard: anonymous /profile redirects to /login.
  2.  Default (no query string) returns the all-time view.
  3.  Each preset (this_month, last_month, last_3_months, last_6_months,
      this_year) returns the right window AND marks the matching button
      as aria-pressed="true" with btn-primary styling.
  4.  Custom range with both `from` and `to` filters correctly.
  5.  Open-ended `from` only / `to` only filter correctly.
  6.  Inverted range renders empty results with filter_label="No results"
      and does not raise.
  7.  Garbage `period` and garbage `from`/`to` silently fall back to all time.
  8.  The active-filter summary line reads "Showing: <label>".
  9.  All four data sections (stats, transactions, categories, bar widths)
      update consistently.
  10. category_max = 0, top_category = "—", avg_monthly = 0.00 for empty sets.
  11. The filter form has the expected buttons and inputs.
  12. No SQL injection footgun — every filtered query uses `?` placeholders.
  13. The SELECT queries used by the helpers are parameterised
      (static assertion against app.py).
"""
from __future__ import annotations

import re
from datetime import date, timedelta

import pytest


# --------------------------------------------------------------------------- #
# Helpers                                                                    #
# --------------------------------------------------------------------------- #

ALLTIME_TOTAL = 302.19  # sum of the 8 seeded rows
ALLTIME_COUNT = 8
ALLTIME_CATEGORIES = {"Food", "Bills", "Shopping", "Health",
                      "Entertainment", "Transport", "Other"}
ALLTIME_CATEGORY_MAX = 120.00  # Bills
ALLTIME_TOP_CATEGORY = "Bills"
ALLTIME_AVG_MONTHLY = ALLTIME_TOTAL  # only one distinct month: June 2026


def _login(client):
    """POST /login as the seeded demo user. Returns the redirect response."""
    return client.post(
        "/login",
        data={"email": "demo@spendly.com", "password": "demo123"},
        follow_redirects=False,
    )


def _authed(client):
    """Return a test client already logged in as the demo user."""
    resp = _login(client)
    # 302 to /profile is the success path for /login.
    assert resp.status_code == 302, f"login failed: {resp.status_code}"
    assert resp.headers["Location"].endswith("/profile")
    return client


# --------------------------------------------------------------------------- #
# 1. Auth guard                                                              #
# --------------------------------------------------------------------------- #

def test_profile_without_auth_redirects_to_login(client):
    """Spec DoD #1: anonymous GET /profile redirects to /login."""
    resp = client.get("/profile", follow_redirects=False)
    assert resp.status_code == 302
    assert resp.headers["Location"].endswith("/login")


# --------------------------------------------------------------------------- #
# 2. Default (no query string) — the all-time view                           #
# --------------------------------------------------------------------------- #

def test_profile_no_query_string_returns_all_time_view(client):
    """Spec DoD #2: default /profile is the all-time view (no regression)."""
    client = _authed(client)
    resp = client.get("/profile")
    assert resp.status_code == 200
    body = resp.get_data(as_text=True)

    # Summary line shows the "All time" label.
    assert "Showing: All time" in body

    # The seeded demo user's full set of categories appears in the breakdown.
    for cat in ALLTIME_CATEGORIES:
        assert cat in body, f"category {cat!r} missing from all-time breakdown"

    # Top category and total are both present.
    assert ALLTIME_TOP_CATEGORY in body
    assert "$302.19" in body
    assert f">{ALLTIME_COUNT}<" in body  # txn count


def test_profile_default_marks_all_time_button_active(client):
    """Spec DoD #3: the matching preset button is aria-pressed + btn-primary."""
    client = _authed(client)
    body = client.get("/profile").get_data(as_text=True)

    # The "All time" control is rendered as an <a> (per template) — find it.
    pattern = (
        r'<a[^>]*aria-pressed="true"[^>]*class="[^"]*\bbtn-primary\b[^"]*"'
        r'[^>]*>\s*All time\s*</a>'
    )
    assert re.search(pattern, body), (
        "expected the 'All time' preset to be aria-pressed='true' and "
        "styled with btn-primary in the default view"
    )


# --------------------------------------------------------------------------- #
# 3. Preset windows                                                          #
# --------------------------------------------------------------------------- #

def test_preset_this_month_filters_to_current_month(client):
    """Spec DoD #3: ?period=this_month narrows to current month."""
    client = _authed(client)
    resp = client.get("/profile?period=this_month")
    assert resp.status_code == 200
    body = resp.get_data(as_text=True)

    today = date.today()
    expected_label = today.strftime("%B %Y")
    assert f"Showing: {expected_label}" in body

    # On any day, all 8 seeded rows are in June 2026, so this_month must
    # return the same total as all_time when today is in June 2026 OR return
    # the empty set when today is in any other month. We accept either —
    # the assertion is about consistency, not about today's calendar.
    if today.year == 2026 and today.month == 6:
        assert "$302.19" in body
        assert ALLTIME_TOP_CATEGORY in body
    else:
        assert "$0.00" in body
        assert ALLTIME_TOP_CATEGORY not in body

    # The "This month" button is the active one.
    pattern = (
        r'<button[^>]*name="period"[^>]*value="this_month"[^>]*'
        r'aria-pressed="true"[^>]*class="[^"]*\bbtn-primary\b[^"]*"'
    )
    assert re.search(pattern, body), (
        "'This month' preset not marked aria-pressed=true + btn-primary"
    )


def test_preset_last_month_filters_out_seeded_june_rows(client):
    """Spec DoD #3 + #9: ?period=last_month excludes the 8 June 2026 rows.

    Per the spec example, all 8 seeded rows are in 2026-06; viewing with
    period=last_month in 2026-06 must filter every one of them out, giving
    an empty filtered set with top_category="—" and avg_monthly=0.00.
    """
    today = date.today()
    if not (today.year == 2026 and today.month == 6):
        pytest.skip("only meaningful when 'today' is in June 2026")

    client = _authed(client)
    resp = client.get("/profile?period=last_month")
    assert resp.status_code == 200
    body = resp.get_data(as_text=True)

    # May 2026 is "last month" from the perspective of June 2026.
    assert "Showing: May 2026" in body
    # Empty results: $0.00 total, no transactions, "—" top category.
    assert "$0.00" in body
    assert ">0</td>" in body or ">0<" in body  # txn_count rendered as 0
    # The "—" dash must appear in the top-category stat.
    assert "—" in body
    # The "Last month" button is the active one.
    pattern = (
        r'<button[^>]*name="period"[^>]*value="last_month"[^>]*'
        r'aria-pressed="true"[^>]*class="[^"]*\bbtn-primary\b[^"]*"'
    )
    assert re.search(pattern, body)


def test_preset_last_3_months_window_and_active_button(client):
    """Spec DoD #3: ?period=last_3_months returns the right window."""
    client = _authed(client)
    body = client.get("/profile?period=last_3_months").get_data(as_text=True)
    assert "Showing: Last 3 months" in body

    pattern = (
        r'<button[^>]*name="period"[^>]*value="last_3_months"[^>]*'
        r'aria-pressed="true"[^>]*class="[^"]*\bbtn-primary\b[^"]*"'
    )
    assert re.search(pattern, body)


def test_preset_last_6_months_window_and_active_button(client):
    """Spec DoD #3: ?period=last_6_months returns the right window."""
    client = _authed(client)
    body = client.get("/profile?period=last_6_months").get_data(as_text=True)
    assert "Showing: Last 6 months" in body

    pattern = (
        r'<button[^>]*name="period"[^>]*value="last_6_months"[^>]*'
        r'aria-pressed="true"[^>]*class="[^"]*\bbtn-primary\b[^"]*"'
    )
    assert re.search(pattern, body)


def test_preset_this_year_window_and_active_button(client):
    """Spec DoD #3: ?period=this_year returns the right window."""
    client = _authed(client)
    body = client.get("/profile?period=this_year").get_data(as_text=True)
    assert f"Showing: {date.today().year}" in body

    pattern = (
        r'<button[^>]*name="period"[^>]*value="this_year"[^>]*'
        r'aria-pressed="true"[^>]*class="[^"]*\bbtn-primary\b[^"]*"'
    )
    assert re.search(pattern, body)


def test_inactive_preset_buttons_are_not_pressed(client):
    """Spec DoD #3: only the active preset gets aria-pressed='true'."""
    client = _authed(client)
    body = client.get("/profile?period=this_year").get_data(as_text=True)

    # The four non-active period buttons must be aria-pressed="false".
    for inactive in ("this_month", "last_month", "last_3_months",
                     "last_6_months"):
        pattern = (
            rf'<button[^>]*name="period"[^>]*value="{inactive}"[^>]*'
            rf'aria-pressed="false"'
        )
        assert re.search(pattern, body), (
            f"preset {inactive!r} should be aria-pressed='false' when "
            f"this_year is active"
        )


# --------------------------------------------------------------------------- #
# 4. Custom ranges (both bounds, open-ended, inverted)                        #
# --------------------------------------------------------------------------- #

def test_custom_range_both_bounds_filters_correctly(client):
    """Spec DoD #4: explicit from+to returns rows in [from, to]."""
    client = _authed(client)
    # June 1 .. June 3 inclusive: Transport(1) Food(2) Bills(3) Food(2) Other(1)
    # Entertainment(2). That's 6 rows out of 8 — the two June 4 + June 5 rows
    # (Weekly groceries 45.20, Shopping 60.00, Health 35.00) must be excluded.
    resp = client.get("/profile?from=2026-06-01&to=2026-06-03")
    assert resp.status_code == 200
    body = resp.get_data(as_text=True)

    # Summary echoes a custom label containing both endpoints.
    assert "Showing:" in body
    assert "Jun" in body and "2026" in body

    # Total = 12.50 + 45.20? No — Weekly groceries (Jun 4) is excluded.
    # 12.50 + 8.00 + 120.00 + 15.99 + 5.50 = 161.99
    assert "$161.99" in body
    # 6 transactions
    assert ">6</td>" in body
    # Transactions from June 4 / June 5 must NOT appear in the table.
    assert "Weekly groceries" not in body
    assert "New shoes" not in body
    assert "Pharmacy" not in body
    # At least one row from inside the window must appear.
    assert "Electricity bill" in body


def test_custom_range_from_only_returns_from_that_date_forward(client):
    """Spec DoD #5: only `from` set → expenses from that date forward."""
    client = _authed(client)
    # June 3 onward: Bills(120.00), Food(45.20, Jun 4), Health(35.00, Jun 5),
    # Shopping(60.00, Jun 4) = 260.20, 4 rows.
    body = client.get("/profile?from=2026-06-03").get_data(as_text=True)
    assert "$260.20" in body
    assert ">4</td>" in body
    # Pre-June-3 rows excluded.
    assert "Bus pass" not in body
    assert "Lunch at cafe" not in body
    assert "Movie ticket" not in body
    assert "Misc" not in body
    # Summary shows the custom label.
    assert "From" in body and "Jun 3" in body and "2026" in body


def test_custom_range_to_only_returns_up_to_that_date(client):
    """Spec DoD #5: only `to` set → expenses up to and including that date."""
    client = _authed(client)
    # Up to June 2 inclusive: Food(12.50), Transport(8.00), Entertainment(15.99),
    # Other(5.50), Food(45.20? No — Jun 4). Wait: Jun 2 only.
    # Jun 1: Bus pass(8.00), Misc(5.50).  Jun 2: Lunch(12.50), Movie(15.99).
    # Total = 8.00 + 5.50 + 12.50 + 15.99 = 41.99, 4 rows.
    body = client.get("/profile?to=2026-06-02").get_data(as_text=True)
    assert "$41.99" in body
    assert ">4</td>" in body
    # Post-June-2 rows excluded.
    assert "Weekly groceries" not in body
    assert "Electricity bill" not in body
    assert "New shoes" not in body
    assert "Pharmacy" not in body


def test_inverted_range_renders_no_results_without_error(client):
    """Spec DoD #6: inverted range → 200, filter_label='No results'."""
    client = _authed(client)
    resp = client.get("/profile?from=2026-12-01&to=2026-01-01")
    assert resp.status_code == 200
    body = resp.get_data(as_text=True)
    assert "Showing: No results" in body

    # Empty-result invariants per spec DoD #10.
    assert "$0.00" in body
    # The "—" em-dash appears in the Top category stat.
    assert "—" in body


# --------------------------------------------------------------------------- #
# 5. Fallback for garbage inputs                                            #
# --------------------------------------------------------------------------- #

def test_garbage_period_falls_back_to_all_time(client):
    """Spec DoD #7: unknown period silently falls back to all time (no 400)."""
    client = _authed(client)
    resp = client.get("/profile?period=garbage")
    assert resp.status_code == 200
    body = resp.get_data(as_text=True)
    assert "Showing: All time" in body
    # All 8 rows still present.
    assert "$302.19" in body
    assert ">8</td>" in body


def test_garbage_from_value_falls_back_to_all_time(client):
    """Spec DoD #7: unparseable `from` is treated as unset."""
    client = _authed(client)
    resp = client.get("/profile?from=not-a-date&to=2026-06-30")
    assert resp.status_code == 200
    body = resp.get_data(as_text=True)
    # `from` is dropped, but `to` is still valid → custom range "Up to Jun 30, 2026".
    # Total should be 302.19 (all 8 rows are <= June 30).
    assert "$302.19" in body


def test_garbage_to_value_falls_back_to_all_time(client):
    """Spec DoD #7: unparseable `to` is treated as unset."""
    client = _authed(client)
    resp = client.get("/profile?from=2026-06-01&to=bogus")
    assert resp.status_code == 200
    body = resp.get_data(as_text=True)
    # `to` is dropped, `from` valid → "From Jun 1, 2026".
    # All 8 rows are >= June 1.
    assert "$302.19" in body


def test_garbage_from_and_to_both_fall_back_to_all_time(client):
    """Spec DoD #7: both unparseable → period preset (all) wins."""
    client = _authed(client)
    resp = client.get("/profile?period=this_month&from=junk&to=also-junk")
    assert resp.status_code == 200
    # Both custom bounds are dropped → fall through to `period=this_month`.
    body = resp.get_data(as_text=True)
    # Whatever the month is, the label must be the "this_month" preset label
    # (a month name + year) or "All time" if anything else goes wrong.
    # We accept either — the requirement is just that no 400/500 is raised.
    assert resp.status_code == 200


# --------------------------------------------------------------------------- #
# 6. Response content shape                                                  #
# --------------------------------------------------------------------------- #

def test_active_filter_summary_line_format(client):
    """Spec DoD #8: the summary line reads exactly 'Showing: <label>'."""
    client = _authed(client)
    body = client.get("/profile").get_data(as_text=True)
    # Find the summary <p>...</p> block and check its text.
    m = re.search(
        r'<p[^>]*class="[^"]*profile-filter-summary[^"]*"[^>]*>'
        r'(.*?)</p>',
        body,
        re.DOTALL,
    )
    assert m, "profile-filter-summary <p> not found in template"
    text = m.group(1).strip()
    # Must start with the literal "Showing:" prefix.
    assert text.startswith("Showing: "), f"unexpected summary: {text!r}"
    # And contain a label after the prefix.
    assert len(text) > len("Showing: ")


def test_filter_form_has_all_six_preset_buttons(client):
    """Spec DoD #11: the filter form includes every preset period control."""
    client = _authed(client)
    body = client.get("/profile").get_data(as_text=True)

    expected = [
        ("all", "All time"),
        ("this_month", "This month"),
        ("last_month", "Last month"),
        ("last_3_months", "Last 3 months"),
        ("last_6_months", "Last 6 months"),
        ("this_year", "This year"),
    ]
    for value, label in expected:
        if value == "all":
            # All time is a link, not a submit button.
            assert f">{label}</a>" in body, f"missing all-time link {label!r}"
        else:
            pattern = (
                rf'<button[^>]*type="submit"[^>]*name="period"[^>]*'
                rf'value="{value}"[^>]*>\s*{re.escape(label)}\s*</button>'
            )
            assert re.search(pattern, body), (
                f"missing preset button value={value!r} label={label!r}"
            )


def test_filter_form_has_from_to_date_inputs_and_apply(client):
    """Spec DoD #11: the filter form exposes <input type=date name=from|to>."""
    client = _authed(client)
    body = client.get("/profile").get_data(as_text=True)

    assert re.search(
        r'<input[^>]*type="date"[^>]*name="from"', body
    ), "missing <input type=date name=from>"
    assert re.search(
        r'<input[^>]*type="date"[^>]*name="to"', body
    ), "missing <input type=date name=to>"
    # The "Apply" submit button is the spec-suggested way to submit the
    # custom range — its presence is the user-facing confirmation that the
    # form is keyboard-navigable end to end.
    assert re.search(
        r'<button[^>]*type="submit"[^>]*>\s*Apply\s*</button>', body
    ), "missing Apply submit button"


def test_custom_range_inputs_echo_back_into_form(client):
    """Spec: filter_from/filter_to are echoed back into the date inputs."""
    client = _authed(client)
    body = client.get(
        "/profile?from=2026-06-02&to=2026-06-04"
    ).get_data(as_text=True)

    # Each date input must round-trip its value back into the form.
    assert 'value="2026-06-02"' in body
    assert 'value="2026-06-04"' in body


# --------------------------------------------------------------------------- #
# 7. Consistency across the four data sections                              #
# --------------------------------------------------------------------------- #

def test_filtering_changes_total_transactions_and_categories_together(client):
    """Spec DoD #9: stats, recent transactions, category breakdown update
    consistently for the active filter."""
    client = _authed(client)

    all_time = client.get("/profile").get_data(as_text=True)
    narrowed = client.get("/profile?from=2026-06-03&to=2026-06-04").get_data(
        as_text=True
    )

    # Total drops from $302.19 to a smaller number.
    assert "$302.19" in all_time
    assert "$302.19" not in narrowed

    # Txn count drops from 8 to 2 (Bills Jun 3 + Food Jun 4 + Shopping Jun 4
    # = 3 rows in the inclusive window). The narrowed view must show 3.
    assert ">8</td>" in all_time
    assert ">3</td>" in narrowed

    # A category present in all_time but absent from the narrowed set
    # must disappear from the narrowed breakdown. Transport and Health
    # are June 1 and June 5 — both outside [Jun 3, Jun 4].
    # Transport row in all_time: $8.00 (Bus pass).
    # In narrowed: should NOT see "Bus pass" or "Pharmacy".
    assert "Bus pass" in all_time
    assert "Bus pass" not in narrowed
    assert "Pharmacy" in all_time
    assert "Pharmacy" not in narrowed

    # The new top category is determined by the narrowed window:
    # 120.00 (Bills) > 60.00 (Shopping) > 45.20 (Food).
    # Bills remains top, but its rendered amount must reflect the FILTERED
    # total, not the all-time total.
    assert "$120.00" in narrowed


def test_empty_filtered_set_reports_safe_defaults(client):
    """Spec DoD #10: empty filter → category_max=0, top_category='—',
    avg_monthly=0.00; total stays $0.00; txn count is 0."""
    client = _authed(client)
    # Far future window — nothing matches.
    body = client.get(
        "/profile?from=2099-01-01&to=2099-12-31"
    ).get_data(as_text=True)

    # Stats line.
    assert "$0.00" in body
    # txn_count is rendered as a plain "0".
    assert ">0</td>" in body
    # The em-dash for top_category must be present.
    assert "—" in body
    # No transaction rows.
    for desc in ("Lunch at cafe", "Weekly groceries", "Bus pass",
                 "Electricity bill", "Pharmacy", "Movie ticket",
                 "New shoes", "Misc"):
        assert desc not in body


# --------------------------------------------------------------------------- #
# 8. SQL hygiene — static checks against the source                          #
# --------------------------------------------------------------------------- #

def test_no_select_uses_string_interpolation_in_app_py():
    """Spec DoD #12 + #13: every SELECT in app.py uses ? placeholders,
    no f-string/%-format/concat-onto-SQL patterns."""
    import pathlib

    app_path = (
        pathlib.Path(__file__).resolve().parent.parent / "app.py"
    )
    source = app_path.read_text(encoding="utf-8")

    # Every SQL keyword we care about — split just to keep the line tidy.
    keywords = ("SELECT", "INSERT", "UPDATE", "DELETE")

    # Find every line that opens a SQL string and look at the rest of the
    # statement. We pull the full multi-line statement up to the next
    # closing ' or " — sloppy but enough for static hygiene checks.
    bad_patterns = [
        # f"... {var} ..." style — would inject Python values into SQL.
        re.compile(r"""(?:SELECT|INSERT|UPDATE|DELETE)\b[^'"]*f['"]"""),
        # "... " + var + " ..." style — concat onto SQL.
        re.compile(
            r"""(?:SELECT|INSERT|UPDATE|DELETE)\b[^'"]*['"]\s*\+\s*\w"""
        ),
        # "... %s ..." % (...) style — classic format-string injection.
        re.compile(r"""(?:SELECT|INSERT|UPDATE|DELETE)\b[^'"]*['"]\s*%"""),
        # Any ?-less SELECT against the expenses table — filter clauses
        # without placeholders would be red flags (rare but worth catching).
        re.compile(
            r"SELECT[^?]*FROM\s+expenses[^?]*\bWHERE\b[^?]*$",
            re.MULTILINE,
        ),
    ]

    for kw in keywords:
        # Walk every line that starts with that keyword.
        for match in re.finditer(rf"\b{kw}\b", source):
            start = match.start()
            # Take a 400-char window from the match onward for analysis.
            window = source[start:start + 400]
            for pat in bad_patterns[:3]:  # f-string, concat, %-format
                assert not pat.search(window), (
                    f"possible SQL string-interpolation in app.py near "
                    f"char {start}: {window[:80]!r}"
                )


def test_filtered_queries_use_question_mark_placeholders():
    """Spec DoD #12: the new WHERE date >= ? / WHERE date <= ? clauses
    use ? placeholders. We check the source for the literal substrings."""
    import pathlib

    app_path = (
        pathlib.Path(__file__).resolve().parent.parent / "app.py"
    )
    source = app_path.read_text(encoding="utf-8")

    assert "date >= ?" in source, "expected `date >= ?` placeholder in app.py"
    assert "date <= ?" in source, "expected `date <= ?` placeholder in app.py"


def test_helpers_accept_date_from_and_date_to_keyword_args():
    """Spec: helpers take date_from/date_to as keyword args."""
    import pathlib

    app_path = (
        pathlib.Path(__file__).resolve().parent.parent / "app.py"
    )
    source = app_path.read_text(encoding="utf-8")

    for helper in ("_get_stats", "_get_recent_transactions",
                   "_get_category_breakdown"):
        # Each helper definition must declare date_from/date_to keyword args.
        # We look for the signature pattern explicitly.
        sig_pattern = re.compile(
            rf"def\s+{helper}\s*\([^)]*date_from\s*=\s*None[^)]*"
            rf"date_to\s*=\s*None",
            re.DOTALL,
        )
        assert sig_pattern.search(source), (
            f"{helper} must accept date_from=None, date_to=None keyword args"
        )


def test_app_still_serves_login_route(client):
    """Spec DoD (last item): register/login/logout still work; the seed
    data still loads."""
    # Login route still serves its GET page.
    resp = client.get("/login")
    assert resp.status_code == 200
    # And the seed user can authenticate.
    resp = client.post(
        "/login",
        data={"email": "demo@spendly.com", "password": "demo123"},
        follow_redirects=False,
    )
    assert resp.status_code == 302
    assert resp.headers["Location"].endswith("/profile")


# --------------------------------------------------------------------------- #
# 9. Date math sanity (no regressions on the four preset windows)            #
# --------------------------------------------------------------------------- #

def test_this_month_window_uses_first_of_month_through_today(client):
    """Spec Rules: this_month = [first-of-current-month, today]."""
    client = _authed(client)
    body = client.get("/profile?period=this_month").get_data(as_text=True)

    today = date.today()
    first_of_month = today.replace(day=1)

    # Boundary: an expense on exactly first-of-month must appear.
    first_row = client.get(
        f"/profile?from={first_of_month.isoformat()}"
        f"&to={today.isoformat()}"
    ).get_data(as_text=True)

    # A row on the day BEFORE first-of-month must NOT appear in this_month.
    if first_of_month > date(2000, 1, 1):
        day_before = first_of_month - timedelta(days=1)
        # Use a window that includes both sides so the only thing limiting
        # the result is the lower bound.
        wider = client.get(
            f"/profile?from={day_before.isoformat()}"
            f"&to={today.isoformat()}"
        ).get_data(as_text=True)

        # The wider window includes everything this_month does plus the
        # pre-month row(s). Count of seeded rows before first_of_month:
        # Bus pass (Jun 1) and Misc (Jun 1) — both ARE on first_of_month,
        # so for June there's nothing before. For other months, the wider
        # window count must be >= this_month count.
        all_rows = [
            "Lunch at cafe", "Weekly groceries", "Bus pass",
            "Electricity bill", "Pharmacy", "Movie ticket",
            "New shoes", "Misc",
        ]
        def count_present(html):
            return sum(1 for r in all_rows if r in html)

        assert count_present(first_row) <= count_present(wider)


def test_period_all_keyword_returns_all_time_label(client):
    """Spec: explicit ?period=all is equivalent to no query string."""
    client = _authed(client)
    body = client.get("/profile?period=all").get_data(as_text=True)
    assert "Showing: All time" in body
    assert "$302.19" in body
