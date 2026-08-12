import json
import sqlite3
from pathlib import Path

from app import auth, sentiment
from app.products import PRODUCTS

DB_PATH = Path(__file__).resolve().parent.parent / "orders.db"


def _connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init():
    with _connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer TEXT NOT NULL DEFAULT 'guest',
                items TEXT NOT NULL,
                total REAL NOT NULL,
                status TEXT NOT NULL DEFAULT 'placed',
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'customer',
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product TEXT NOT NULL,
                author TEXT NOT NULL,
                rating INTEGER NOT NULL,
                text TEXT NOT NULL,
                sentiment TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
            """
        )
        # migrate pre-existing orders table that lacks the customer column
        cols = {r["name"] for r in conn.execute("PRAGMA table_info(orders)")}
        if "customer" not in cols:
            conn.execute("ALTER TABLE orders ADD COLUMN customer TEXT NOT NULL DEFAULT 'guest'")
    _seed()


def _row_to_order(row: sqlite3.Row) -> dict:
    return {
        "id": row["id"],
        "customer": row["customer"],
        "items": json.loads(row["items"]),
        "total": row["total"],
        "status": row["status"],
        "created_at": row["created_at"],
    }


def create_order(items: list, total: float, customer: str = "guest") -> dict:
    with _connect() as conn:
        cur = conn.execute(
            "INSERT INTO orders (customer, items, total) VALUES (?, ?, ?)",
            (customer, json.dumps(items), total),
        )
        order_id = cur.lastrowid
    return get_order(order_id)


def get_order(order_id: int) -> dict | None:
    with _connect() as conn:
        row = conn.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()
    return _row_to_order(row) if row else None


def list_orders_by_customer(email: str) -> list[dict]:
    with _connect() as conn:
        rows = conn.execute(
            "SELECT * FROM orders WHERE customer = ? ORDER BY created_at DESC", (email,)
        ).fetchall()
    return [_row_to_order(r) for r in rows]


def purchased_products(email: str) -> set[str]:
    """Product names in this customer's non-cancelled orders (what they may review)."""
    names = set()
    for o in list_orders_by_customer(email):
        if o["status"] != "cancelled":
            names.update(i["name"] for i in o["items"])
    return names


def cancel_order(order_id: int) -> dict | None:
    with _connect() as conn:
        conn.execute("UPDATE orders SET status = 'cancelled' WHERE id = ?", (order_id,))
    return get_order(order_id)


# --- admin order CRUD ---

def list_orders() -> list[dict]:
    with _connect() as conn:
        rows = conn.execute("SELECT * FROM orders ORDER BY created_at DESC").fetchall()
    return [_row_to_order(r) for r in rows]


def update_order(order_id: int, status: str) -> dict | None:
    with _connect() as conn:
        conn.execute("UPDATE orders SET status = ? WHERE id = ?", (status, order_id))
    return get_order(order_id)


def delete_order(order_id: int) -> bool:
    with _connect() as conn:
        cur = conn.execute("DELETE FROM orders WHERE id = ?", (order_id,))
    return cur.rowcount > 0


# --- users ---

def get_user_by_email(email: str) -> dict | None:
    with _connect() as conn:
        row = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    return dict(row) if row else None


def display_name(email: str) -> str:
    """Map a login email to its seeded display name; fall back to the email."""
    names = {ADMIN[0]: ADMIN[2], **{e: n for e, _pw, n in GUESTS}}
    return names.get(email, email)


# --- reviews ---

def list_reviews() -> list[dict]:
    with _connect() as conn:
        rows = conn.execute("SELECT * FROM reviews ORDER BY created_at DESC").fetchall()
    return [dict(r) for r in rows]


def add_review(product: str, author: str, rating: int, text: str) -> dict:
    with _connect() as conn:
        cur = conn.execute(
            "INSERT INTO reviews (product, author, rating, text, sentiment) VALUES (?, ?, ?, ?, ?)",
            (product, author, rating, text, sentiment.classify(text)),
        )
        rid = cur.lastrowid
        row = conn.execute("SELECT * FROM reviews WHERE id = ?", (rid,)).fetchone()
    return dict(row)


# --- analytics for the dashboard ---

def analytics() -> dict:
    with _connect() as conn:
        orders = conn.execute(
            "SELECT COUNT(*) n, COALESCE(SUM(total), 0) rev FROM orders WHERE status != 'cancelled'"
        ).fetchone()
        status = conn.execute(
            "SELECT status, COUNT(*) n FROM orders GROUP BY status"
        ).fetchall()
        sent = conn.execute(
            "SELECT sentiment, COUNT(*) n FROM reviews GROUP BY sentiment"
        ).fetchall()
    return {
        "orders": {"count": orders["n"], "revenue": round(orders["rev"], 2)},
        "status": {r["status"]: r["n"] for r in status},
        "sentiment": {r["sentiment"]: r["n"] for r in sent},
        "reviews_total": sum(r["n"] for r in sent),
    }


# --- seed: idempotent, only fills empty tables ---

CREDENTIALS_PATH = DB_PATH.parent / "CREDENTIALS.txt"

# (email, password, display_name). Admin first, then 10 guests.
ADMIN = ("admin@novagoods.com", "admin123", "Store Admin")
GUESTS = [
    ("guest1@novagoods.com", "guest1pw", "Ava Chen"),
    ("guest2@novagoods.com", "guest2pw", "Ben Ortiz"),
    ("guest3@novagoods.com", "guest3pw", "Cara Diaz"),
    ("guest4@novagoods.com", "guest4pw", "Dan Whitfield"),
    ("guest5@novagoods.com", "guest5pw", "Eli Park"),
    ("guest6@novagoods.com", "guest6pw", "Faye Romano"),
    ("guest7@novagoods.com", "guest7pw", "Gus Hall"),
    ("guest8@novagoods.com", "guest8pw", "Hana Kim"),
    ("guest9@novagoods.com", "guest9pw", "Ian Cole"),
    ("guest10@novagoods.com", "guest10pw", "Joy Nash"),
]

_SEED_REVIEWS = [
    ("Aurora Wireless Earbuds", "Ava Chen", 5, "Absolutely love these, great sound and the battery works all day."),
    ("Aurora Wireless Earbuds", "Ben Ortiz", 2, "Disappointing, one earbud stopped working after a week. Waste of money."),
    ("Aurora Wireless Earbuds", "Cara Diaz", 4, "Nice fit and reliable connection, happy with the purchase."),
    ("Bassline Over-Ear Headphones", "Dan Whitfield", 5, "Fantastic noise cancelling and comfortable cups, best headphones I have owned."),
    ("Bassline Over-Ear Headphones", "Eli Park", 3, "They are fine, sound is okay but nothing amazing for the price."),
    ("PocketBoom Bluetooth Speaker", "Faye Romano", 5, "Impressed by the sound, durable and truly waterproof, would recommend."),
    ("PocketBoom Bluetooth Speaker", "Gus Hall", 2, "Poor bass and the battery drains fast, a bit disappointing."),
    ("Echo Clip Mini Speaker", "Hana Kim", 1, "Terrible, the clip broke on day one and it is useless now."),
    ("Pulse Smart Watch", "Ian Cole", 4, "Solid tracking and reliable battery, satisfied overall."),
    ("Pulse Smart Watch", "Joy Nash", 2, "The screen is defective and the app is annoying to set up."),
    ("Zenith Fitness Band", "Ava Chen", 5, "Great little band, comfortable and the step tracking works perfectly."),
    ("Zenith Fitness Band", "Ben Ortiz", 3, "It does the job, accuracy is average."),
    ("Drifter Canvas Backpack", "Cara Diaz", 5, "Excellent quality and comfortable straps, would recommend to anyone."),
    ("Drifter Canvas Backpack", "Dan Whitfield", 4, "Good sturdy bag, the laptop sleeve is nicely padded."),
    ("Metro Messenger Bag", "Eli Park", 2, "Flimsy strap and the flap magnet is weak, felt overpriced."),
    ("Trailhead 40L Duffel", "Faye Romano", 5, "Durable and roomy, the straps are a wonderful touch for travel."),
    ("Stride Running Sneakers", "Gus Hall", 1, "Terrible, uncomfortable and fell apart fast, had to return them."),
    ("CloudStep Walking Shoes", "Hana Kim", 5, "So comfortable, the memory foam is amazing for long walks."),
    ("CloudStep Walking Shoes", "Ian Cole", 4, "Nice shoes, good grip and reliable for daily wear."),
    ("Summit Trail Boots", "Joy Nash", 5, "Waterproof and solid on rough trails, worth every penny."),
    ("Summit Trail Boots", "Ava Chen", 2, "The sole started peeling after a month, poor durability."),
    ("Lumos LED Desk Lamp", "Ben Ortiz", 4, "Nice lamp, good brightness levels and it works perfectly."),
    ("Terra Ceramic Mug", "Cara Diaz", 1, "Broke on the second day, poor quality and useless now."),
    ("Terra Ceramic Mug", "Dan Whitfield", 5, "Lovely mug, keeps coffee warm and feels great in the hand."),
    ("Nimbus Knit Throw Blanket", "Eli Park", 5, "Wonderfully soft and warm, my favorite blanket now."),
    ("Ember Soy Candle", "Faye Romano", 3, "Pleasant scent but the burn time is shorter than expected."),
    ("Clicky Mechanical Keyboard", "Gus Hall", 5, "Best keyboard I have owned, fantastic switches and solid build."),
    ("Clicky Mechanical Keyboard", "Hana Kim", 2, "Overpriced and the backlight was defective on arrival."),
    ("Volt 10K Power Bank", "Ian Cole", 5, "Fast charging and durable, impressed with the quality."),
    ("Glide Wireless Mouse", "Joy Nash", 4, "Silent clicks are great and it feels reliable, happy with it."),
    ("Glide Wireless Mouse", "Ava Chen", 2, "Cursor stutters and the scroll wheel feels cheap and flimsy."),
    ("SnapView 1080p Webcam", "Ben Ortiz", 1, "Awful image quality and the mic stopped working, waste of money."),
    ("Grippy Yoga Mat", "Cara Diaz", 3, "Standard mat, it is fine for the price."),
    ("Grippy Yoga Mat", "Dan Whitfield", 5, "Excellent grip and comfortable, recommend for daily practice."),
    ("HydroCore Steel Bottle", "Eli Park", 5, "Keeps drinks cold all day, durable and well made."),
    ("IronFlex Resistance Bands", "Faye Romano", 4, "Good set of bands, solid quality and versatile."),
    ("PowerGrip Dumbbell Set", "Gus Hall", 2, "The quick-lock plates are faulty and rattle, disappointing."),
    ("Solstice Polarized Sunglasses", "Hana Kim", 4, "Nice polarized lenses, comfortable and stylish."),
    ("Nomad Leather Wallet", "Ian Cole", 5, "Beautiful leather and solid stitching, worth it."),
    ("Chrono Minimalist Watch", "Joy Nash", 5, "Elegant and reliable, a wonderful everyday watch."),
    ("Chrono Minimalist Watch", "Ava Chen", 2, "Strap felt cheap and it stopped ticking within weeks."),
]

# (customer_name, [(product, qty)], status)
_SEED_ORDERS = [
    ("Ava Chen", [("Aurora Wireless Earbuds", 1), ("Terra Ceramic Mug", 2)], "placed"),
    ("Ben Ortiz", [("Bassline Over-Ear Headphones", 1)], "shipped"),
    ("Cara Diaz", [("Drifter Canvas Backpack", 1), ("HydroCore Steel Bottle", 1)], "placed"),
    ("Dan Whitfield", [("Clicky Mechanical Keyboard", 1), ("Glide Wireless Mouse", 1)], "shipped"),
    ("Eli Park", [("Nimbus Knit Throw Blanket", 2)], "cancelled"),
    ("Faye Romano", [("Summit Trail Boots", 1), ("IronFlex Resistance Bands", 1)], "placed"),
    ("Gus Hall", [("PocketBoom Bluetooth Speaker", 1)], "shipped"),
    ("Hana Kim", [("Solstice Polarized Sunglasses", 1), ("Nomad Leather Wallet", 1)], "placed"),
    ("Ian Cole", [("Volt 10K Power Bank", 2), ("Grippy Yoga Mat", 1)], "shipped"),
    ("Joy Nash", [("Chrono Minimalist Watch", 1)], "cancelled"),
]


def _write_credentials():
    lines = ["Nova Goods — test accounts", "=" * 30, "",
             "ADMIN (can access /admin dashboard)",
             f"  email:    {ADMIN[0]}", f"  password: {ADMIN[1]}", "",
             "GUESTS (role: customer)"]
    for email, pw, name in GUESTS:
        lines.append(f"  {name:<16} email: {email:<24} password: {pw}")
    CREDENTIALS_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _price(name: str) -> float:
    return next(p["price"] for p in PRODUCTS if p["name"] == name)


def _seed():
    names = {p["name"] for p in PRODUCTS}
    with _connect() as conn:
        if conn.execute("SELECT COUNT(*) n FROM users").fetchone()["n"] == 0:
            conn.execute("INSERT INTO users (email, password_hash, role) VALUES (?, ?, 'admin')",
                         (ADMIN[0], auth.hash_password(ADMIN[1])))
            for email, pw, _name in GUESTS:
                conn.execute("INSERT INTO users (email, password_hash, role) VALUES (?, ?, 'customer')",
                             (email, auth.hash_password(pw)))
            _write_credentials()
        if conn.execute("SELECT COUNT(*) n FROM reviews").fetchone()["n"] == 0:
            for product, author, rating, text in _SEED_REVIEWS:
                assert product in names, f"seed review for unknown product: {product}"
                conn.execute(
                    "INSERT INTO reviews (product, author, rating, text, sentiment) VALUES (?, ?, ?, ?, ?)",
                    (product, author, rating, text, sentiment.classify(text)),
                )
        if conn.execute("SELECT COUNT(*) n FROM orders").fetchone()["n"] == 0:
            name_to_email = {n: e for e, _pw, n in GUESTS}
            for customer, lines, status in _SEED_ORDERS:
                items = [{"name": n, "price": _price(n), "qty": q} for n, q in lines]
                total = round(sum(i["price"] * i["qty"] for i in items), 2)
                conn.execute(
                    "INSERT INTO orders (customer, items, total, status) VALUES (?, ?, ?, ?)",
                    (name_to_email.get(customer, customer), json.dumps(items), total, status),
                )
