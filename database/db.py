"""SQLite data layer for Spendly.

Three functions only:
    get_db()   — returns a connection with row_factory + FK enforcement
    init_db()  — creates users and expenses tables (idempotent)
    seed_db()  — inserts one demo user and 8 sample expenses (idempotent)
"""
import sqlite3
from pathlib import Path

from werkzeug.security import generate_password_hash

# Project root is one level up from this file (database/).
DB_PATH = (Path(__file__).resolve().parent.parent / "expense_tracker.db")


def get_db():
    """Open a connection with Row factory and foreign key enforcement enabled."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """Create both tables. Safe to call on every startup."""
    conn = get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            name          TEXT    NOT NULL,
            email         TEXT    UNIQUE NOT NULL,
            password_hash TEXT    NOT NULL,
            created_at    TEXT    NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS expenses (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER NOT NULL REFERENCES users(id),
            amount      REAL    NOT NULL,
            category    TEXT    NOT NULL,
            date        TEXT    NOT NULL,
            description TEXT,
            created_at  TEXT    NOT NULL DEFAULT (datetime('now'))
        );
    """)
    conn.commit()
    conn.close()


def seed_db():
    """Insert demo user + 8 sample expenses. No-op if users already has rows."""
    conn = get_db()

    if conn.execute("SELECT COUNT(*) FROM users").fetchone()[0] > 0:
        conn.close()
        return

    conn.execute(
        "INSERT INTO users(name, email, password_hash) VALUES (?, ?, ?)",
        ("Demo User", "demo@spendly.com", generate_password_hash("demo123")),
    )
    user_id = conn.execute(
        "SELECT id FROM users WHERE email = ?", ("demo@spendly.com",)
    ).fetchone()["id"]

    # (amount, category, date, description)
    expenses = [
        (12.50, "Food",          "2026-06-02", "Lunch at cafe"),
        (45.20, "Food",          "2026-06-04", "Weekly groceries"),
        (8.00,  "Transport",     "2026-06-01", "Bus pass"),
        (120.00,"Bills",         "2026-06-03", "Electricity bill"),
        (35.00, "Health",        "2026-06-05", "Pharmacy"),
        (15.99, "Entertainment", "2026-06-02", "Movie ticket"),
        (60.00, "Shopping",      "2026-06-04", "New shoes"),
        (5.50,  "Other",         "2026-06-01", "Misc"),
    ]
    conn.executemany(
        "INSERT INTO expenses(user_id, amount, category, date, description) "
        "VALUES (?, ?, ?, ?, ?)",
        [(user_id, amount, category, date, description)
         for amount, category, date, description in expenses],
    )
    conn.commit()
    conn.close()
