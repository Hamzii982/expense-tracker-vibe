import math
import os
import sqlite3
from datetime import datetime, date, timedelta

from flask import Flask, render_template, request, redirect, url_for, session

from database.db import get_db, init_db, seed_db

# check_password_hash is imported for Step 3 (Login) — kept here so the
# import block doesn't change again next step.
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY") or "dev-only-change-me"

with app.app_context():
    init_db()
    seed_db()


# ------------------------------------------------------------------ #
# Constants                                                           #
# ------------------------------------------------------------------ #

# Whitelisted expense categories — shared by the add_expense view, the
# add_expense template, and any future edit form. Order is the order
# the template renders them in. Matches the categories used by the
# seeded data so freshly added rows colour correctly in the category
# breakdown on /profile.
EXPENSE_CATEGORIES = (
    "Food",
    "Transport",
    "Bills",
    "Health",
    "Entertainment",
    "Shopping",
    "Other",
)


# ------------------------------------------------------------------ #
# Routes                                                              #
# ------------------------------------------------------------------ #

@app.route("/")
def landing():
    return render_template("landing.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if session.get("user_id"):
        return redirect(url_for("profile"))

    if request.method == "POST":
        name = (request.form.get("name") or "").strip()
        email = (request.form.get("email") or "").strip()
        password = (request.form.get("password") or "").strip()

        # 1. All three fields present and non-empty after .strip().
        if not name or not email or not password:
            return render_template("register.html", error="all fields are required"), 400

        # 2. Light email shape check: exactly one '@', non-empty parts.
        if email.count("@") != 1:
            return render_template("register.html", error="please enter a valid email address"), 400
        local, domain = email.split("@")
        if not local or not domain:
            return render_template("register.html", error="please enter a valid email address"), 400

        # 3. Password length >= 8.
        if len(password) < 8:
            return render_template("register.html", error="password must be at least 8 characters"), 400

        conn = get_db()

        # Case-insensitive duplicate check — Alice@x.com and alice@x.com collide.
        existing = conn.execute(
            "SELECT 1 FROM users WHERE lower(email) = lower(?)",
            (email,),
        ).fetchone()
        if existing is not None:
            conn.close()
            return render_template("register.html", error="email already registered"), 400

        # Belt-and-braces: the UNIQUE index on email also catches a
        # concurrent insert that slipped past the SELECT above.
        try:
            cursor = conn.execute(
                "INSERT INTO users(name, email, password_hash) VALUES (?, ?, ?)",
                (name, email, generate_password_hash(password)),
            )
            conn.commit()
            user_id = cursor.lastrowid
        except sqlite3.IntegrityError:
            conn.close()
            return render_template("register.html", error="email already registered"), 400

        conn.close()

        session["user_id"] = user_id
        session["user_name"] = name
        return redirect(url_for("profile"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("user_id"):
        return redirect(url_for("profile"))

    if request.method == "POST":
        email = (request.form.get("email") or "").strip()
        password = (request.form.get("password") or "").strip()

        if not email or not password:
            return render_template("login.html", error="all fields are required"), 400

        conn = get_db()
        user = conn.execute(
            "SELECT * FROM users WHERE lower(email) = lower(?)",
            (email,),
        ).fetchone()
        conn.close()

        if user is None or not check_password_hash(user["password_hash"], password):
            return render_template("login.html", error="invalid email or password"), 400

        session["user_id"] = user["id"]
        session["user_name"] = user["name"]
        return redirect(url_for("profile"))

    return render_template("login.html")

@app.route("/terms")
def terms():
    return render_template("terms.html")


@app.route("/privacy")
def privacy():
    return render_template("privacy.html")


@app.route("/analytics")
def analytics():
    if not session.get("user_id"):
        return redirect(url_for("login"))
    return render_template("analytics.html")


# ------------------------------------------------------------------ #
# Placeholder routes — students will implement these                  #
# ------------------------------------------------------------------ #

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("landing"))

@app.route("/profile")
def profile():
    if not session.get("user_id"):
        return redirect(url_for("login"))

    flt = _resolve_date_range(request.args)
    date_from, date_to = flt["date_from"], flt["date_to"]

    conn = get_db()

    user = _get_user(conn, session["user_id"])
    if user is None:
        conn.close()
        session.clear()
        return redirect(url_for("login"))

    stats = _get_stats(
        conn, session["user_id"], date_from=date_from, date_to=date_to
    )
    transactions = _get_recent_transactions(
        conn, session["user_id"], date_from=date_from, date_to=date_to
    )
    category_breakdown, category_max = _get_category_breakdown(
        conn, session["user_id"], date_from=date_from, date_to=date_to
    )

    conn.close()

    return render_template(
        "profile.html",
        user=user,
        stats=stats,
        transactions=transactions,
        category_breakdown=category_breakdown,
        category_max=category_max,
        filter_label=flt["filter_label"],
        active_period=flt["active_period"],
        filter_from=flt["from_raw"],
        filter_to=flt["to_raw"],
    )


# ------------------------------------------------------------------ #
# Profile view helpers                                                #
# ------------------------------------------------------------------ #

# Preset periods accepted on the /profile query string. Anything else
# in `period` falls back to "all" silently (per spec Definition of done).
_PERIOD_KEYS = {
    "all",
    "this_month",
    "last_month",
    "last_3_months",
    "last_6_months",
    "this_year",
}


def _resolve_date_range(args):
    """Parse /profile's query string into a concrete date range.

    Returns a dict with:
        date_from, date_to : date | None   — bounds passed to the DB helpers
        active_period      : str           — which preset is highlighted
        filter_label       : str           — "Showing: <label>" copy
        from_raw, to_raw   : str | None    — for echoing into the date inputs
    """
    period = (args.get("period") or "all").strip()
    if period not in _PERIOD_KEYS:
        period = "all"

    from_raw = (args.get("from") or "").strip()
    to_raw = (args.get("to") or "").strip()

    from_d = _parse_iso(from_raw)
    to_d = _parse_iso(to_raw)

    # An explicit custom range beats the period preset.
    if from_d is not None or to_d is not None:
        if from_d is not None and to_d is not None and from_d > to_d:
            # Inverted range — spec: empty results, "No results" label.
            # Pass the inverted bounds through to the helpers; SQLite's
            # `WHERE date >= '2026-12-01' AND date <= '2026-01-01'` is
            # guaranteed to match zero rows.
            return {
                "date_from": from_d,
                "date_to": to_d,
                "active_period": "custom",
                "filter_label": "No results",
                "from_raw": from_raw,
                "to_raw": to_raw,
            }
        return {
            "date_from": from_d,
            "date_to": to_d,
            "active_period": "custom",
            "filter_label": _format_custom_label(from_d, to_d),
            "from_raw": from_raw,
            "to_raw": to_raw,
        }

    today = date.today()
    first_of_month = today.replace(day=1)

    if period == "all":
        return {
            "date_from": None,
            "date_to": None,
            "active_period": "all",
            "filter_label": "All time",
            "from_raw": None,
            "to_raw": None,
        }

    if period == "this_month":
        return {
            "date_from": first_of_month,
            "date_to": today,
            "active_period": "this_month",
            "filter_label": today.strftime("%B %Y"),
            "from_raw": None,
            "to_raw": None,
        }

    if period == "last_month":
        last_day_of_prev = first_of_month - timedelta(days=1)
        first_of_prev = last_day_of_prev.replace(day=1)
        return {
            "date_from": first_of_prev,
            "date_to": last_day_of_prev,
            "active_period": "last_month",
            "filter_label": last_day_of_prev.strftime("%B %Y"),
            "from_raw": None,
            "to_raw": None,
        }

    if period in ("last_3_months", "last_6_months"):
        n = 3 if period == "last_3_months" else 6
        # Start from the last day of the previous month, then walk back
        # (n - 2) more times — each step lands on the last day of the
        # month-before. From there, rewind to the first of that month.
        # For n=3 that means April 1 (current + 2 previous full months);
        # for n=6 it means January 1 (current + 5 previous full months).
        d = first_of_month - timedelta(days=1)
        for _ in range(n - 2):
            d = d.replace(day=1) - timedelta(days=1)
        range_from = d.replace(day=1)
        return {
            "date_from": range_from,
            "date_to": today,
            "active_period": period,
            "filter_label": f"Last {n} months",
            "from_raw": None,
            "to_raw": None,
        }

    if period == "this_year":
        return {
            "date_from": today.replace(month=1, day=1),
            "date_to": today,
            "active_period": "this_year",
            "filter_label": str(today.year),
            "from_raw": None,
            "to_raw": None,
        }


def _parse_iso(value):
    """Return date.fromisoformat(value) or None on any failure."""
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except (TypeError, ValueError):
        return None


def _format_custom_label(from_d, to_d):
    """Render a human label for an explicit from/to range."""
    if from_d is not None and to_d is not None:
        if from_d.year == to_d.year:
            return f"{_short(from_d)} – {_short(to_d, with_year=True)}"
        return f"{_short(from_d, with_year=True)} – {_short(to_d, with_year=True)}"
    if from_d is not None:
        return f"From {_short(from_d, with_year=True)}"
    if to_d is not None:
        return f"Up to {_short(to_d, with_year=True)}"
    return "All time"


def _short(d, *, with_year=False):
    """`Jun 22` / `Jun 22, 2026` without a leading zero on the day."""
    suffix = f", {d.year}" if with_year else ""
    return f"{d.strftime('%b')} {d.day}{suffix}"


def _date_where(date_from, date_to):
    """Build a (clause_fragment, params) pair for a date range filter.

    Returns ("", []) when no bounds are set so the "all time" path stays
    byte-identical to the pre-filter SQL.
    """
    clauses, params = [], []
    if date_from is not None:
        clauses.append("date >= ?")
        params.append(date_from.isoformat())
    if date_to is not None:
        clauses.append("date <= ?")
        params.append(date_to.isoformat())
    if not clauses:
        return "", []
    return " AND " + " AND ".join(clauses), params


def _get_user(conn, user_id):
    row = conn.execute(
        "SELECT name, email, created_at FROM users WHERE id = ?",
        (user_id,),
    ).fetchone()
    if row is None:
        return None
    parts = row["name"].split()
    initials = "".join(p[0] for p in parts[:2]).upper() or "?"
    joined = datetime.strptime(row["created_at"], "%Y-%m-%d %H:%M:%S").strftime("%B %Y")
    return {
        "name": row["name"],
        "email": row["email"],
        "initials": initials,
        "joined": joined,
    }


def _get_stats(conn, user_id, *, date_from=None, date_to=None):
    extra, extra_params = _date_where(date_from, date_to)

    total_spent = conn.execute(
        "SELECT COALESCE(SUM(amount), 0) FROM expenses WHERE user_id = ?"
        + extra,
        (user_id, *extra_params),
    ).fetchone()[0]

    txn_count = conn.execute(
        "SELECT COUNT(*) FROM expenses WHERE user_id = ?"
        + extra,
        (user_id, *extra_params),
    ).fetchone()[0]

    top_row = conn.execute(
        "SELECT category FROM expenses WHERE user_id = ?"
        + extra
        + " GROUP BY category ORDER BY SUM(amount) DESC LIMIT 1",
        (user_id, *extra_params),
    ).fetchone()
    top_category = top_row["category"] if top_row is not None else "—"

    month_count = conn.execute(
        "SELECT COUNT(DISTINCT substr(date, 1, 7)) FROM expenses WHERE user_id = ?"
        + extra,
        (user_id, *extra_params),
    ).fetchone()[0]
    avg_monthly = round(total_spent / month_count, 2) if month_count else 0.0

    return {
        "total_spent": total_spent,
        "txn_count": txn_count,
        "top_category": top_category,
        "avg_monthly": avg_monthly,
    }


def _get_recent_transactions(conn, user_id, *, limit=8, date_from=None, date_to=None):
    extra, extra_params = _date_where(date_from, date_to)
    rows = conn.execute(
        "SELECT date, description, category, amount FROM expenses "
        "WHERE user_id = ?"
        + extra
        + " ORDER BY date DESC, id DESC LIMIT ?",
        (user_id, *extra_params, limit),
    ).fetchall()
    return [dict(r) for r in rows]


def _get_category_breakdown(conn, user_id, *, date_from=None, date_to=None):
    extra, extra_params = _date_where(date_from, date_to)
    rows = conn.execute(
        "SELECT category AS name, SUM(amount) AS total "
        "FROM expenses WHERE user_id = ?"
        + extra
        + " GROUP BY category ORDER BY total DESC",
        (user_id, *extra_params),
    ).fetchall()
    breakdown = [dict(row) for row in rows]
    category_max = max((c["total"] for c in breakdown), default=0)
    return breakdown, category_max


@app.route("/expenses/add", methods=["GET", "POST"])
def add_expense():
    if not session.get("user_id"):
        return redirect(url_for("login"))

    # Default context — first render, no submission, no error.
    context = {
        "today": date.today().isoformat(),
        "categories": EXPENSE_CATEGORIES,
        "form": {
            "amount": "",
            "category": "",
            "date": date.today().isoformat(),
            "description": "",
        },
        "error": "",
    }

    if request.method == "POST":
        # 1. Read & strip.
        amount_raw = (request.form.get("amount") or "").strip()
        category = (request.form.get("category") or "").strip()
        date_raw = (request.form.get("date") or "").strip()
        description = (request.form.get("description") or "").strip()

        # Echo submitted values back into the form on any failure.
        context["form"] = {
            "amount": amount_raw,
            "category": category,
            "date": date_raw,
            "description": description,
        }

        # 2. Validate amount — parseable, positive, under the sanity cap.
        amount_value = None
        try:
            amount_value = float(amount_raw)
        except (TypeError, ValueError):
            context["error"] = "amount must be a number"
            return render_template("add_expense.html", **context), 400
        # nan and inf parse as floats but are not valid expense amounts.
        if not math.isfinite(amount_value):
            context["error"] = "amount must be a number"
            return render_template("add_expense.html", **context), 400
        if amount_value <= 0:
            context["error"] = "amount must be greater than 0"
            return render_template("add_expense.html", **context), 400
        if amount_value > 1_000_000:
            context["error"] = "amount must be 1,000,000 or less"
            return render_template("add_expense.html", **context), 400

        # 3. Validate category — must be in the whitelist.
        if category not in EXPENSE_CATEGORIES:
            context["error"] = "please pick a category"
            return render_template("add_expense.html", **context), 400

        # 4. Validate date — ISO YYYY-MM-DD, not in the future.
        if not date_raw:
            context["error"] = "please pick a date"
            return render_template("add_expense.html", **context), 400
        try:
            parsed_date = date.fromisoformat(date_raw)
        except (TypeError, ValueError):
            context["error"] = "please enter a valid date"
            return render_template("add_expense.html", **context), 400
        if parsed_date > date.today():
            context["error"] = "date can't be in the future"
            return render_template("add_expense.html", **context), 400

        # 5. Validate description — optional, stripped, max 200 chars.
        if len(description) > 200:
            context["error"] = "description must be 200 characters or less"
            return render_template("add_expense.html", **context), 400
        description_value = description or None

        # 6. Insert. user_id is bound from session, never from the form.
        conn = get_db()
        conn.execute(
            "INSERT INTO expenses(user_id, amount, category, date, description) "
            "VALUES (?, ?, ?, ?, ?)",
            (
                session["user_id"],
                amount_value,
                category,
                parsed_date.isoformat(),
                description_value,
            ),
        )
        conn.commit()
        conn.close()

        return redirect(url_for("profile"))

    return render_template("add_expense.html", **context)


@app.route("/expenses/<int:id>/edit")
def edit_expense(id):
    return "Edit expense — coming in Step 8"


@app.route("/expenses/<int:id>/delete")
def delete_expense(id):
    return "Delete expense — coming in Step 9"


if __name__ == "__main__":
    app.run(debug=True, port=5001)
