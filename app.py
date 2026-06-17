import os
import sqlite3

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

    user = {
        "name": "Demo User",
        "email": "demo@spendly.com",
        "initials": "DU",
        "joined": "May 2026",
    }

    stats = {
        "total_spent": 302.19,
        "txn_count": 8,
        "top_category": "Bills",
        "avg_monthly": 302.19,
    }

    transactions = [
        {"date": "2026-06-05", "description": "Pharmacy",          "category": "Health",        "amount": 35.00},
        {"date": "2026-06-04", "description": "Weekly groceries",  "category": "Food",          "amount": 45.20},
        {"date": "2026-06-04", "description": "New shoes",         "category": "Shopping",      "amount": 60.00},
        {"date": "2026-06-03", "description": "Electricity bill",  "category": "Bills",         "amount": 120.00},
        {"date": "2026-06-02", "description": "Lunch at cafe",     "category": "Food",          "amount": 12.50},
        {"date": "2026-06-02", "description": "Movie ticket",      "category": "Entertainment", "amount": 15.99},
        {"date": "2026-06-01", "description": "Bus pass",          "category": "Transport",     "amount": 8.00},
        {"date": "2026-06-01", "description": "Misc",              "category": "Other",         "amount": 5.50},
    ]

    category_breakdown = [
        {"name": "Food",          "total": 57.70},
        {"name": "Transport",     "total": 8.00},
        {"name": "Bills",         "total": 120.00},
        {"name": "Health",        "total": 35.00},
        {"name": "Entertainment", "total": 15.99},
        {"name": "Shopping",      "total": 60.00},
        {"name": "Other",         "total": 5.50},
    ]
    category_max = max(c["total"] for c in category_breakdown)

    return render_template(
        "profile.html",
        user=user,
        stats=stats,
        transactions=transactions,
        category_breakdown=category_breakdown,
        category_max=category_max,
    )


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
