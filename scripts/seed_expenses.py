"""Seed realistic dummy expenses for a specific user.

Usage: python scripts/seed_expenses.py <user_id> <count> <months>
"""
import random
import sys
from datetime import date, timedelta
from pathlib import Path

# Make 'database' package importable when run from repo root
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from database.db import get_db  # noqa: E402

# (category, amount_low, amount_high, relative_weight, sample_descriptions)
CATEGORIES = [
    ("Food",          50,   800,
     30,
     [
         "Lunch at Haldiram's", "Chai and samosa", "Swiggy order - Biryani",
         "Domino's pizza", "Subway sandwich", "Weekly groceries at BigBasket",
         "Breakfast at Indian Coffee House", "Zomato - Butter Chicken",
         "Street food at Chowpatty", "Dinner at Saravana Bhavan",
     ]),
    ("Transport",     20,   500,
     20,
     [
         "Uber to office", "Auto rickshaw", "Metro card recharge",
         "Ola ride to airport", "Petrol refill", "Rapido bike ride",
         "Local bus pass", "Diesel for car", "Train ticket to Pune",
         "Parking at mall",
     ]),
    ("Bills",         200,  3000,
     12,
     [
         "Electricity bill - BSES", "Airtel mobile recharge",
         "Broadband - Jio Fiber", "Gas cylinder refill",
         "Water bill - municipal", "DTH recharge - Tata Play",
         "Credit card statement", "Maintenance charge - society",
         "Insurance premium - LIC", "Netflix subscription",
     ]),
    ("Health",        100,  2000,
     7,
     [
         "Pharmacy - Apollo", "Doctor consultation",
         "Lab tests - Thyrocare", "Dental cleaning",
         "Health supplement", "Eye checkup at Lenskart",
         "Ayurvedic medicine", "Gym membership - monthly",
     ]),
    ("Entertainment", 100,  1500,
     8,
     [
         "Movie ticket - PVR", "BookMyShow - concert",
         "Spotify Premium", "Disney+ Hotstar", "PUBG UC top-up",
         "Steam game purchase", "Bookstore - Crossword",
         "Board game cafe", "Stand-up comedy show",
     ]),
    ("Shopping",      200,  5000,
     15,
     [
         "Amazon - headphones", "Flipkart - t-shirt", "Myntra - kurta",
         "Croma - phone case", "Decathlon - yoga mat",
         "IKEA - bookshelf", "Lifestyle - shoes", "Nykaa - cosmetics",
         "D-Mart - household items", "Ajio - jeans",
     ]),
    ("Other",         50,   1000,
     8,
     [
         "Haircut at salon", "Gift for friend's birthday",
         "Donation to temple", "Photocopying at stationery",
         "Laundry - dhobi", "Tailor - alteration",
         "Newspaper subscription", "Pet supplies",
     ]),
]


def pick_weighted_category():
    total = sum(w for _, _, _, w, _ in CATEGORIES)
    r = random.uniform(0, total)
    cum = 0
    for cat, lo, hi, w, descs in CATEGORIES:
        cum += w
        if r <= cum:
            return cat, lo, hi, descs
    return CATEGORIES[-1][:4]  # pragma: no cover


def random_date_in_past_months(months: int) -> str:
    today = date.today()
    days_back = random.randint(0, months * 30)
    return (today - timedelta(days=days_back)).isoformat()


def main():
    if len(sys.argv) != 4:
        print("Usage: python scripts/seed_expenses.py <user_id> <count> <months>")
        print("Example: python scripts/seed_expenses.py 1 50 6")
        sys.exit(1)

    user_id = int(sys.argv[1])
    count = int(sys.argv[2])
    months = int(sys.argv[3])

    conn = get_db()
    try:
        user = conn.execute(
            "SELECT id, name, email FROM users WHERE id = ?", (user_id,)
        ).fetchone()
        if user is None:
            print(f"No user found with id {user_id}.")
            sys.exit(1)

        rows = []
        for _ in range(count):
            cat, lo, hi, descs = pick_weighted_category()
            amount = round(random.uniform(lo, hi), 2)
            description = random.choice(descs)
            d = random_date_in_past_months(months)
            rows.append((user_id, amount, cat, d, description))

        try:
            conn.executemany(
                "INSERT INTO expenses(user_id, amount, category, date, description) "
                "VALUES (?, ?, ?, ?, ?)",
                rows,
            )
            conn.commit()
        except Exception as e:
            conn.rollback()
            print(f"Insert failed, rolled back: {e}")
            sys.exit(1)

        inserted = conn.execute(
            "SELECT id, amount, category, date, description "
            "FROM expenses WHERE user_id = ? ORDER BY date ASC",
            (user_id,),
        ).fetchall()

        dates = [r["date"] for r in inserted]
        print(f"Inserted {len(inserted)} expenses for user {user_id} "
              f"({user['name']} <{user['email']}>)")
        print(f"Date range: {min(dates)} -> {max(dates)}")
        print("\nSample of 5 inserted records:")
        sample = random.sample(inserted, k=min(5, len(inserted)))
        for r in sample:
            print(f"  #{r['id']:>3}  {r['date']}  ₹{r['amount']:>7.2f}  "
                  f"{r['category']:<14} {r['description']}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
