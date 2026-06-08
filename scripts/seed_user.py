"""One-off script: insert a random Indian user into users.

Idempotent on schema only (not on rows) — re-running will pick a different
random name/email each time and skip inserts when the chosen email already
exists.
"""
import random
import sys
from datetime import datetime
from pathlib import Path

# Make the project root importable so we can use database.db.get_db()
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from werkzeug.security import generate_password_hash

from database.db import get_db, init_db

# Regional mix — North, South, East, West, Central — covers the linguistic
# spread you'd plausibly see in a personal app's user base.
FIRST_NAMES = [
    "Aarav", "Vihaan", "Aditya", "Arjun", "Rohan",        # North
    "Ishaan", "Karan", "Rahul", "Yash", "Vikram",
    "Aanya", "Diya", "Priya", "Neha", "Pooja",             # North (female)
    "Rohan", "Karthik", "Arun", "Vijay", "Suresh",         # South
    "Anjali", "Lakshmi", "Divya", "Meera", "Kavya",
    "Ravi", "Sanjay", "Amit", "Nikhil", "Pranav",          # Pan-India
]
LAST_NAMES = [
    "Sharma", "Verma", "Gupta", "Agarwal", "Mishra",       # North
    "Reddy", "Iyer", "Nair", "Pillai", "Rao", "Naidu",     # South
    "Mukherjee", "Banerjee", "Chatterjee", "Das", "Bose",  # East
    "Patel", "Shah", "Desai", "Mehta", "Joshi", "Modi",    # West
    "Khan", "Siddiqui", "Ansari", "Qureshi",               # Pan-India
]
DOMAINS = ["gmail.com", "yahoo.com", "outlook.com", "hotmail.com"]


def _make_email(first: str, last: str) -> str:
    suffix = random.randint(10, 999)
    return f"{first.lower()}{last.lower()}{suffix}@{random.choice(DOMAINS)}"


def main() -> None:
    # Ensure schema exists. Safe to call repeatedly.
    init_db()

    conn = get_db()
    try:
        # Loop until we land on an unused email.
        for _ in range(50):
            first = random.choice(FIRST_NAMES)
            last = random.choice(LAST_NAMES)
            email = _make_email(first, last)
            taken = conn.execute(
                "SELECT 1 FROM users WHERE email = ?", (email,)
            ).fetchone()
            if not taken:
                break
        else:
            raise RuntimeError("Couldn't find an unused email after 50 tries")

        password_hash = generate_password_hash("password123")
        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        cur = conn.execute(
            "INSERT INTO users(name, email, password_hash, created_at) "
            "VALUES (?, ?, ?, ?)",
            (f"{first} {last}", email, password_hash, created_at),
        )
        conn.commit()
        user_id = cur.lastrowid

        print(f"id      : {user_id}")
        print(f"name    : {first} {last}")
        print(f"email   : {email}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
