import os
import sqlite3
from datetime import datetime

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

    conn = get_db()

    user = _get_user(conn, session["user_id"])
    if user is None:
        conn.close()
        session.clear()
        return redirect(url_for("login"))

    stats = _get_stats(conn, session["user_id"])
    transactions = _get_recent_transactions(conn, session["user_id"])
    category_breakdown, category_max = _get_category_breakdown(conn, session["user_id"])

    conn.close()

    return render_template(
        "profile.html",
        user=user,
        stats=stats,
        transactions=transactions,
        category_breakdown=category_breakdown,
        category_max=category_max,
    )


# ------------------------------------------------------------------ #
# Profile view helpers                                                #
# ------------------------------------------------------------------ #

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


def _get_stats(conn, user_id):
    total_spent = conn.execute(
        "SELECT COALESCE(SUM(amount), 0) FROM expenses WHERE user_id = ?",
        (user_id,),
    ).fetchone()[0]

    txn_count = conn.execute(
        "SELECT COUNT(*) FROM expenses WHERE user_id = ?",
        (user_id,),
    ).fetchone()[0]

    top_row = conn.execute(
        "SELECT category FROM expenses WHERE user_id = ? "
        "GROUP BY category ORDER BY SUM(amount) DESC LIMIT 1",
        (user_id,),
    ).fetchone()
    top_category = top_row["category"] if top_row is not None else "—"

    month_count = conn.execute(
        "SELECT COUNT(DISTINCT substr(date, 1, 7)) FROM expenses WHERE user_id = ?",
        (user_id,),
    ).fetchone()[0]
    avg_monthly = round(total_spent / month_count, 2) if month_count else 0.0

    return {
        "total_spent": total_spent,
        "txn_count": txn_count,
        "top_category": top_category,
        "avg_monthly": avg_monthly,
    }


def _get_recent_transactions(conn, user_id, limit=8):
    rows = conn.execute(
        "SELECT date, description, category, amount FROM expenses "
        "WHERE user_id = ? ORDER BY date DESC, id DESC LIMIT ?",
        (user_id, limit),
    ).fetchall()
    return [dict(r) for r in rows]


def _get_category_breakdown(conn, user_id):
    rows = conn.execute(
        "SELECT category AS name, SUM(amount) AS total "
        "FROM expenses WHERE user_id = ? "
        "GROUP BY category ORDER BY total DESC",
        (user_id,),
    ).fetchall()
    breakdown = [dict(row) for row in rows]
    category_max = max((c["total"] for c in breakdown), default=0)
    return breakdown, category_max


@app.route("/expenses/add")
def add_expense():
    return "Add expense — coming in Step 7"


@app.route("/expenses/<int:id>/edit")
def edit_expense(id):
    return "Edit expense — coming in Step 8"


@app.route("/expenses/<int:id>/delete")
def delete_expense(id):
    return "Delete expense — coming in Step 9"


if __name__ == "__main__":
    app.run(debug=True, port=5001)
