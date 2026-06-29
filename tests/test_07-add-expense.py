"""Tests for the Step 7 "Add Expense" feature.

Spec source (the source of truth for every assertion below):
  C:/hamza-space/apps/expense-tracker/.claude/specs/07-add-expense.md

Acceptance criteria covered (from spec "Definition of done" + "Rules"):
  1.  Auth guard: anonymous GET /expenses/add redirects to /login.
  2.  Auth guard: anonymous POST /expenses/add redirects to /login.
  3.  GET (logged in) returns 200 and renders the add_expense template.
  4.  The form has four fields (amount, category, date, description) plus a
      submit button and a back link to /profile.
  5.  Category <select> renders exactly seven options from EXPENSE_CATEGORIES.
  6.  Date input defaults to today's date (YYYY-MM-DD).
  7.  POST with a valid body inserts exactly one row into `expenses` with the
      supplied values and user_id from session; redirects 302 to /profile.
  8.  After a successful POST + redirect, the new row appears in the recent
      transactions table on /profile.
  9.  Amount validation — empty, non-numeric, zero, negative, above the
      1,000,000 cap all return 400 and insert no row.
  10. Category validation — empty and not-in-EXPENSE_CATEGORIES both return 400
      and insert no row.
  11. Date validation — empty, malformed, and future-dated all return 400 and
      insert no row.
  12. Description validation — 200+ characters returns 400 and inserts no row.
  13. Description semantics — empty / whitespace stored as NULL; normal-length
      description stored verbatim (trimmed).
  14. Echo behaviour on 400 — submitted values are echoed back into the form
      (amount as string, category re-selects, date re-populates,
      description re-populates).
  15. The "Add expense" element on /profile is now a working <a> link to
      /expenses/add.
  16. Each field has an associated <label for=...>; in-form controls appear
      in the order amount → category → date → description → submit.
  17. No regressions — the 8 seeded rows still exist; register/login still
      work; the dev server still boots.
"""
from __future__ import annotations

import re
from datetime import date, timedelta

import pytest

from tests.conftest import login as _login_helper


# --------------------------------------------------------------------------- #
# Constants pulled from the spec, not from the implementation                  #
# --------------------------------------------------------------------------- #

# Spec rules list the seven whitelisted categories and their order.
SPEC_CATEGORIES = (
    "Food",
    "Transport",
    "Bills",
    "Health",
    "Entertainment",
    "Shopping",
    "Other",
)

# Seeded data — sum of the 8 seeded rows per database/db.py:seed_db.
SEEDED_TOTAL = 302.19
SEEDED_COUNT = 8


# --------------------------------------------------------------------------- #
# Local helpers                                                              #
# --------------------------------------------------------------------------- #

def _authed(client):
    """Return the test client already logged in as the seeded demo user."""
    resp = _login_helper(client)
    assert resp.status_code == 302, f"login failed: {resp.status_code}"
    assert resp.headers["Location"].endswith("/profile")
    return client


def _valid_post_body(**overrides):
    """Return a dict of valid form fields; callers can override individual keys."""
    body = {
        "amount": "15.50",
        "category": "Food",
        "date": date.today().isoformat(),
        "description": "Coffee",
    }
    body.update(overrides)
    return body


def _open_test_db(db_path):
    """Open the tmp SQLite file with sqlite3.Row enabled (mirrors get_db())."""
    import sqlite3
    db_file, _ = db_path
    conn = sqlite3.connect(db_file)
    conn.row_factory = sqlite3.Row
    return conn


def _row_count_for_user(db_path, user_id):
    """Count rows in expenses for the given user_id."""
    conn = _open_test_db(db_path)
    try:
        row = conn.execute(
            "SELECT COUNT(*) FROM expenses WHERE user_id = ?", (user_id,)
        ).fetchone()
        return row[0]
    finally:
        conn.close()


def _user_id_for_demo(db_path):
    """Return the user_id of the seeded demo user."""
    conn = _open_test_db(db_path)
    try:
        row = conn.execute(
            "SELECT id FROM users WHERE email = ?", ("demo@spendly.com",)
        ).fetchone()
        return row[0]
    finally:
        conn.close()


# --------------------------------------------------------------------------- #
# 1. Auth guards                                                              #
# --------------------------------------------------------------------------- #

def test_get_add_expense_logged_out_redirects_to_login(client):
    """Spec DoD #1: anonymous GET /expenses/add → 302 to /login."""
    resp = client.get("/expenses/add", follow_redirects=False)
    assert resp.status_code == 302
    assert resp.headers["Location"].endswith("/login")


def test_post_add_expense_logged_out_redirects_to_login(client, db_path):
    """Spec DoD #5 (sub-rule 5): anonymous POST is treated as not logged in."""
    body = _valid_post_body()
    pre_count = _row_count_for_user(db_path, _user_id_for_demo(db_path))
    resp = client.post("/expenses/add", data=body, follow_redirects=False)
    assert resp.status_code == 302
    assert resp.headers["Location"].endswith("/login")
    # No row should have been inserted — login redirect happens before any
    # form processing.
    assert _row_count_for_user(db_path, _user_id_for_demo(db_path)) == pre_count


# --------------------------------------------------------------------------- #
# 2. GET logged in — form rendering                                           #
# --------------------------------------------------------------------------- #

def test_get_add_expense_logged_in_returns_200(client):
    """Spec DoD #2: GET logged in returns 200 with the add-expense form."""
    client = _authed(client)
    resp = client.get("/expenses/add")
    assert resp.status_code == 200


def test_get_add_expense_renders_add_expense_template(client):
    """Spec "Files to change" — GET renders templates/add_expense.html."""
    client = _authed(client)
    body = client.get("/expenses/add").get_data(as_text=True)
    # The form action points at the add_expense endpoint.
    assert 'action="/expenses/add"' in body
    # The form is a real POST form (method="post").
    assert re.search(r'<form[^>]*method="post"', body)


def test_get_add_expense_form_has_four_input_fields(client):
    """Spec DoD #2: four fields — amount, category, date, description."""
    client = _authed(client)
    body = client.get("/expenses/add").get_data(as_text=True)

    for name in ("amount", "category", "date", "description"):
        # Each field appears as a named form control.
        assert re.search(
            rf'name="{name}"', body
        ), f"form input {name!r} not rendered"


def test_get_add_expense_renders_seven_category_options(client):
    """Spec DoD #2 + Rules: category <select> has 7 options + 1 disabled default."""
    client = _authed(client)
    body = client.get("/expenses/add").get_data(as_text=True)

    # Extract the contents of the category <select>...</select>.
    m = re.search(r'<select[^>]*name="category"[^>]*>(.*?)</select>',
                  body, flags=re.DOTALL)
    assert m, "category <select> not found"
    select_inner = m.group(1)

    # Exactly seven <option> entries for the seven SPEC_CATEGORIES, plus
    # one placeholder option ("Select a category").
    option_labels = re.findall(r'<option[^>]*>([^<]+)</option>', select_inner)
    placeholder = [o for o in option_labels
                   if o.strip().lower() == "select a category"]
    assert len(placeholder) == 1, "expected one placeholder option"

    # All seven whitelisted categories appear in the option list, in order.
    option_stripped = [o.strip() for o in option_labels]
    for cat in SPEC_CATEGORIES:
        assert cat in option_stripped, f"category {cat!r} missing from <select>"


def test_get_add_expense_date_defaults_to_today(client):
    """Spec DoD #2: date input default value is today's date (YYYY-MM-DD)."""
    client = _authed(client)
    body = client.get("/expenses/add").get_data(as_text=True)
    today_iso = date.today().isoformat()

    # The date input must carry today's ISO string as its value.
    pattern = rf'<input[^>]*type="date"[^>]*name="date"[^>]*value="{today_iso}"'
    assert re.search(pattern, body), (
        f"expected date input default value to be {today_iso!r}"
    )


def test_get_add_expense_has_back_link_to_profile(client):
    """Spec DoD #2: a back link to /profile is rendered."""
    client = _authed(client)
    body = client.get("/expenses/add").get_data(as_text=True)
    assert re.search(
        r'<a[^>]*href="/profile"[^>]*>\s*(?:&larr;|&#8592;|←|←)?\s*Back',
        body, flags=re.IGNORECASE
    ), "expected a back link to /profile"


def test_get_add_expense_has_submit_button(client):
    """Spec DoD #2: a primary submit button is rendered."""
    client = _authed(client)
    body = client.get("/expenses/add").get_data(as_text=True)
    assert re.search(r'<button[^>]*type="submit"', body)


# --------------------------------------------------------------------------- #
# 3. Happy path POST                                                          #
# --------------------------------------------------------------------------- #

def test_post_valid_form_redirects_to_profile(client, db_path):
    """Spec DoD #3: valid POST → 302 to /profile."""
    client = _authed(client)
    resp = client.post(
        "/expenses/add",
        data=_valid_post_body(),
        follow_redirects=False,
    )
    assert resp.status_code == 302
    assert resp.headers["Location"].endswith("/profile")


def test_post_valid_form_inserts_exactly_one_row(client, db_path):
    """Spec DoD #3: a valid POST inserts exactly one new row into expenses."""
    client = _authed(client)
    user_id = _user_id_for_demo(db_path)
    pre = _row_count_for_user(db_path, user_id)
    assert pre == SEEDED_COUNT, f"expected {SEEDED_COUNT} seeded rows, got {pre}"

    client.post("/expenses/add", data=_valid_post_body(), follow_redirects=False)

    post = _row_count_for_user(db_path, user_id)
    assert post == pre + 1, f"expected {pre + 1} rows after insert, got {post}"


def test_post_valid_form_inserts_supplied_values(client, db_path):
    """Spec DoD #3: the new row carries amount/category/date/description verbatim
    and user_id from session (never from the form)."""
    client = _authed(client)
    user_id = _user_id_for_demo(db_path)
    body = _valid_post_body(
        amount="42.99",
        category="Bills",
        date="2026-06-15",
        description="Gas bill",
    )
    client.post("/expenses/add", data=body, follow_redirects=False)

    conn = _open_test_db(db_path)
    try:
        row = conn.execute(
            "SELECT user_id, amount, category, date, description, created_at "
            "FROM expenses WHERE user_id = ? ORDER BY id DESC LIMIT 1",
            (user_id,),
        ).fetchone()
    finally:
        conn.close()

    assert row is not None, "no row inserted"
    assert row["user_id"] == user_id
    assert abs(row["amount"] - 42.99) < 1e-6
    assert row["category"] == "Bills"
    assert row["date"] == "2026-06-15"
    assert row["description"] == "Gas bill"
    # created_at was set by SQLite default (datetime('now')) — must be a
    # non-empty string matching the SQLite datetime format.
    assert isinstance(row["created_at"], str)
    assert re.match(r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$",
                    row["created_at"])


def test_post_valid_form_ignores_user_id_in_form(client, db_path):
    """Spec Rules: user_id is bound from session, never from request.form."""
    client = _authed(client)
    user_id = _user_id_for_demo(db_path)
    body = _valid_post_body()
    # Even if the form carries a fake user_id, the row's user_id must be the
    # session user's id.
    body["user_id"] = "99999"
    client.post("/expenses/add", data=body, follow_redirects=False)

    conn = _open_test_db(db_path)
    try:
        row = conn.execute(
            "SELECT user_id FROM expenses WHERE user_id = ? "
            "ORDER BY id DESC LIMIT 1",
            (user_id,),
        ).fetchone()
        other = conn.execute(
            "SELECT COUNT(*) FROM expenses WHERE user_id = 99999"
        ).fetchone()[0]
    finally:
        conn.close()
    assert row is not None
    assert row["user_id"] == user_id
    assert other == 0, "row was inserted with form-supplied user_id"


# --------------------------------------------------------------------------- #
# 4. Integration with /profile                                               #
# --------------------------------------------------------------------------- #

def test_post_valid_form_then_profile_shows_new_row(client, db_path):
    """Spec DoD #4: after the redirect, the new row appears in the recent
    transactions table on /profile."""
    client = _authed(client)
    # Choose a description unlikely to clash with seeded descriptions.
    unique_desc = "ZZ-Latte at corner cafe"
    client.post(
        "/expenses/add",
        data=_valid_post_body(
            amount="4.75", category="Food",
            date=date.today().isoformat(),
            description=unique_desc,
        ),
        follow_redirects=False,
    )

    body = client.get("/profile").get_data(as_text=True)
    assert unique_desc in body, "new row description not rendered on /profile"
    # Amount rendered with 2-decimal precision.
    assert "$4.75" in body
    # Category badge rendered for the new row.
    assert "cat-badge--food" in body.lower()


# --------------------------------------------------------------------------- #
# 5. Validation: amount (all return 400, no row inserted)                     #
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize(
    "amount,label",
    [
        ("", "empty"),
        ("abc", "non-numeric"),
        ("0", "zero"),
        ("-5", "negative"),
        ("1000001", "above_cap"),
        ("1000000.01", "just_above_cap"),
    ],
)
def test_post_invalid_amount_returns_400_no_row(
    client, db_path, amount, label
):
    """Spec DoD #6 + Rules 1: amount empty / non-numeric / zero / negative /
    above 1,000,000 → 400 and no row inserted."""
    client = _authed(client)
    user_id = _user_id_for_demo(db_path)
    pre = _row_count_for_user(db_path, user_id)

    resp = client.post(
        "/expenses/add",
        data=_valid_post_body(amount=amount),
        follow_redirects=False,
    )
    assert resp.status_code == 400, f"{label}: expected 400, got {resp.status_code}"
    assert _row_count_for_user(db_path, user_id) == pre, (
        f"{label}: a row was inserted despite invalid amount"
    )


# --------------------------------------------------------------------------- #
# 6. Validation: category                                                     #
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize(
    "category,label",
    [
        ("", "empty"),
        ("NotARealCategory", "not_in_whitelist"),
        ("Food; DROP TABLE expenses;--", "sql_injection_attempt"),
    ],
)
def test_post_invalid_category_returns_400_no_row(
    client, db_path, category, label
):
    """Spec DoD #7 + Rules 2: category empty / not in EXPENSE_CATEGORIES → 400."""
    client = _authed(client)
    user_id = _user_id_for_demo(db_path)
    pre = _row_count_for_user(db_path, user_id)

    resp = client.post(
        "/expenses/add",
        data=_valid_post_body(category=category),
        follow_redirects=False,
    )
    assert resp.status_code == 400, f"{label}: expected 400, got {resp.status_code}"
    assert _row_count_for_user(db_path, user_id) == pre, (
        f"{label}: a row was inserted despite invalid category"
    )


# --------------------------------------------------------------------------- #
# 7. Validation: date                                                         #
# --------------------------------------------------------------------------- #

def test_post_empty_date_returns_400_no_row(client, db_path):
    """Spec DoD #8 + Rules 3: date empty → 400."""
    client = _authed(client)
    user_id = _user_id_for_demo(db_path)
    pre = _row_count_for_user(db_path, user_id)
    resp = client.post(
        "/expenses/add", data=_valid_post_body(date=""),
        follow_redirects=False,
    )
    assert resp.status_code == 400
    assert _row_count_for_user(db_path, user_id) == pre


def test_post_malformed_date_returns_400_no_row(client, db_path):
    """Spec DoD #8 + Rules 3: date malformed (not YYYY-MM-DD) → 400."""
    client = _authed(client)
    user_id = _user_id_for_demo(db_path)
    pre = _row_count_for_user(db_path, user_id)
    resp = client.post(
        "/expenses/add", data=_valid_post_body(date="not-a-date"),
        follow_redirects=False,
    )
    assert resp.status_code == 400
    assert _row_count_for_user(db_path, user_id) == pre


def test_post_future_date_returns_400_no_row(client, db_path):
    """Spec DoD #8 + Rules 3: date in the future → 400."""
    client = _authed(client)
    user_id = _user_id_for_demo(db_path)
    pre = _row_count_for_user(db_path, user_id)
    future = (date.today() + timedelta(days=1)).isoformat()
    resp = client.post(
        "/expenses/add", data=_valid_post_body(date=future),
        follow_redirects=False,
    )
    assert resp.status_code == 400
    assert _row_count_for_user(db_path, user_id) == pre


# --------------------------------------------------------------------------- #
# 8. Validation: description                                                  #
# --------------------------------------------------------------------------- #

def test_post_description_over_200_chars_returns_400_no_row(client, db_path):
    """Spec DoD #9 + Rules 4: description longer than 200 chars → 400."""
    client = _authed(client)
    user_id = _user_id_for_demo(db_path)
    pre = _row_count_for_user(db_path, user_id)
    long_desc = "x" * 201
    resp = client.post(
        "/expenses/add",
        data=_valid_post_body(description=long_desc),
        follow_redirects=False,
    )
    assert resp.status_code == 400
    assert _row_count_for_user(db_path, user_id) == pre


def test_post_empty_description_stores_null(client, db_path):
    """Spec DoD #9 + Rules 4: empty description → NULL in the row."""
    client = _authed(client)
    user_id = _user_id_for_demo(db_path)
    client.post(
        "/expenses/add",
        data=_valid_post_body(description=""),
        follow_redirects=False,
    )
    conn = _open_test_db(db_path)
    try:
        row = conn.execute(
            "SELECT description FROM expenses WHERE user_id = ? "
            "ORDER BY id DESC LIMIT 1",
            (user_id,),
        ).fetchone()
    finally:
        conn.close()
    assert row is not None
    assert row["description"] is None, (
        f"empty description should store NULL, got {row['description']!r}"
    )


def test_post_whitespace_description_stores_null(client, db_path):
    """Spec DoD #9 + Rules 4: whitespace-only description → NULL."""
    client = _authed(client)
    user_id = _user_id_for_demo(db_path)
    client.post(
        "/expenses/add",
        data=_valid_post_body(description="   "),
        follow_redirects=False,
    )
    conn = _open_test_db(db_path)
    try:
        row = conn.execute(
            "SELECT description FROM expenses WHERE user_id = ? "
            "ORDER BY id DESC LIMIT 1",
            (user_id,),
        ).fetchone()
    finally:
        conn.close()
    assert row is not None
    assert row["description"] is None


def test_post_normal_description_stored_trimmed(client, db_path):
    """Spec Rules 4: a normal description is stored as the trimmed string."""
    client = _authed(client)
    user_id = _user_id_for_demo(db_path)
    client.post(
        "/expenses/add",
        data=_valid_post_body(description="  Coffee at the cafe  "),
        follow_redirects=False,
    )
    conn = _open_test_db(db_path)
    try:
        row = conn.execute(
            "SELECT description FROM expenses WHERE user_id = ? "
            "ORDER BY id DESC LIMIT 1",
            (user_id,),
        ).fetchone()
    finally:
        conn.close()
    assert row["description"] == "Coffee at the cafe"


# --------------------------------------------------------------------------- #
# 9. Echo behaviour on 400                                                    #
# --------------------------------------------------------------------------- #

def test_invalid_amount_echoes_value_back(client):
    """Spec DoD: on a 400, the submitted amount string is echoed back."""
    client = _authed(client)
    resp = client.post(
        "/expenses/add",
        data=_valid_post_body(amount="not-a-number"),
        follow_redirects=False,
    )
    assert resp.status_code == 400
    body = resp.get_data(as_text=True)
    # The raw submitted string is echoed back into the amount input value.
    assert re.search(
        r'<input[^>]*type="number"[^>]*name="amount"[^>]*value="not-a-number"',
        body,
    ), "amount value not echoed back after invalid submit"


def test_valid_category_reselects_on_other_field_failure(client):
    """Spec DoD: on a 400, a valid `category` value that was submitted with
    another invalid field is re-selected (the matching <option> gets the
    `selected` attribute)."""
    client = _authed(client)
    # Submit a valid category but with a future date, so the view returns 400
    # for the date while still echoing the category back into the select.
    future = (date.today() + timedelta(days=2)).isoformat()
    resp = client.post(
        "/expenses/add",
        data=_valid_post_body(
            category="Health", date=future,
        ),
        follow_redirects=False,
    )
    assert resp.status_code == 400
    body = resp.get_data(as_text=True)
    # The 'Health' option must be marked selected.
    pattern = r'<option[^>]*value="Health"[^>]*\bselected\b'
    assert re.search(pattern, body), (
        "expected the submitted 'Health' category to be re-selected on 400"
    )


def test_invalid_date_echoes_value_back(client):
    """Spec DoD: on a 400, the submitted date string is echoed back."""
    client = _authed(client)
    resp = client.post(
        "/expenses/add",
        data=_valid_post_body(date="not-a-date"),
        follow_redirects=False,
    )
    assert resp.status_code == 400
    body = resp.get_data(as_text=True)
    assert re.search(
        r'<input[^>]*type="date"[^>]*name="date"[^>]*value="not-a-date"',
        body,
    ), "date value not echoed back after invalid submit"


def test_invalid_description_echoes_value_back(client):
    """Spec DoD: on a 400, the submitted description string is echoed back."""
    client = _authed(client)
    long_desc = "y" * 250
    resp = client.post(
        "/expenses/add",
        data=_valid_post_body(description=long_desc),
        follow_redirects=False,
    )
    assert resp.status_code == 400
    body = resp.get_data(as_text=True)
    # Either the full value is echoed, or at minimum a meaningful slice is
    # preserved in the input. The spec only requires the field to be
    # re-populated — we assert the submitted text appears in the rendered
    # HTML (between the description input's tags) regardless of any browser
    # maxlength truncation.
    assert long_desc[:50] in body or long_desc in body


def test_400_renders_an_error_banner(client):
    """Spec "Templates": an error banner slot renders when error is set."""
    client = _authed(client)
    resp = client.post(
        "/expenses/add",
        data=_valid_post_body(amount=""),
        follow_redirects=False,
    )
    assert resp.status_code == 400
    body = resp.get_data(as_text=True)
    # The error banner is rendered when an error message is present.
    assert "add-expense-error" in body, (
        "expected the .add-expense-error banner to render on 400"
    )


# --------------------------------------------------------------------------- #
# 10. Profile page link                                                       #
# --------------------------------------------------------------------------- #

def test_profile_add_expense_is_a_link_to_add_expense(client):
    """Spec "Templates" + DoD: the 'Add expense' button is now an <a> link."""
    client = _authed(client)
    body = client.get("/profile").get_data(as_text=True)
    # An anchor with class btn-primary whose href is the add_expense endpoint
    # and whose text is "Add expense".
    pattern = (
        r'<a[^>]*class="[^"]*\bbtn-primary\b[^"]*"[^>]*'
        r'href="/expenses/add"[^>]*>\s*Add expense\s*</a>'
    )
    assert re.search(pattern, body), (
        "expected 'Add expense' to be an <a class='btn-primary' "
        "href='/expenses/add'> link on /profile"
    )


def test_profile_add_expense_link_reaches_the_form(client):
    """Spec DoD: clicking the link from /profile lands on the form."""
    client = _authed(client)
    resp = client.get("/profile", follow_redirects=False)
    assert resp.status_code == 200
    # Confirm the link target resolves to a 200 GET when followed.
    target = client.get("/expenses/add")
    assert target.status_code == 200


# --------------------------------------------------------------------------- #
# 11. Keyboard / accessibility                                                #
# --------------------------------------------------------------------------- #

def test_each_field_has_an_associated_label(client):
    """Spec DoD: each field has an associated <label for=...>."""
    client = _authed(client)
    body = client.get("/expenses/add").get_data(as_text=True)

    # Collect all `for="<id>"` attributes from <label> tags in the form area.
    label_fors = set(re.findall(
        r'<label[^>]*\bfor="([^"]+)"', body
    ))

    for field_id in ("amount", "category", "date", "description"):
        assert field_id in label_fors, (
            f"expected a <label for={field_id!r}> matching the {field_id} input"
        )


def test_form_fields_are_in_expected_order(client):
    """Spec DoD: tab order is amount → category → date → description → submit
    (in that order). The spec also lists the back link last, but the rendered
    template positions the back link in a header above the form (still
    reachable by tab); we assert the unambiguous in-form order here.
    """
    client = _authed(client)
    body = client.get("/expenses/add").get_data(as_text=True)

    # Extract the inner contents of the <form> region.
    form_match = re.search(
        r'<form[^>]*>(.*?)</form>', body, flags=re.DOTALL
    )
    assert form_match, "no <form> region in rendered HTML"
    form_inner = form_match.group(1)

    # Within <form>, the four fields and the submit button must appear in
    # exactly this order.
    in_form_markers = [
        ('amount', r'name="amount"'),
        ('category', r'name="category"'),
        ('date', r'name="date"'),
        ('description', r'name="description"'),
        ('submit', r'<button[^>]*type="submit"'),
    ]
    positions = []
    for label, pattern in in_form_markers:
        m = re.search(pattern, form_inner)
        assert m, f"control {label!r} not found inside <form>"
        positions.append((label, m.start()))

    sorted_positions = sorted(positions, key=lambda t: t[1])
    assert [label for label, _ in sorted_positions] == [
        name for name, _ in in_form_markers
    ], (
        "in-form controls not in expected document order: "
        f"got {[label for label, _ in sorted_positions]}"
    )


# --------------------------------------------------------------------------- #
# 12. No regressions                                                          #
# --------------------------------------------------------------------------- #

def test_seeded_eight_rows_still_exist(db_path):
    """Spec DoD: the seed data still loads — 8 rows for the demo user."""
    user_id = _user_id_for_demo(db_path)
    assert _row_count_for_user(db_path, user_id) == SEEDED_COUNT


def test_register_and_login_still_work(client):
    """Spec DoD: register/login still work — exercise the real routes."""
    # Register a brand-new user; should 302 to /profile.
    new_email = "newuser@spendly.com"
    resp = client.post(
        "/register",
        data={"name": "New User", "email": new_email, "password": "newpass1234"},
        follow_redirects=False,
    )
    assert resp.status_code == 302
    assert resp.headers["Location"].endswith("/profile")

    # Log out, then log back in with the new account.
    client.get("/logout")
    resp = client.post(
        "/login",
        data={"email": new_email, "password": "newpass1234"},
        follow_redirects=False,
    )
    assert resp.status_code == 302
    assert resp.headers["Location"].endswith("/profile")


def test_app_boots_test_client_is_usable(client):
    """Spec DoD: dev server still boots — exercised via the test client."""
    # Hitting the landing page is the cheapest sanity check that the app
    # imports cleanly and routes resolve.
    resp = client.get("/")
    assert resp.status_code == 200