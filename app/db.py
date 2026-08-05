import json
import sqlite3
from pathlib import Path

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
                items TEXT NOT NULL,
                total REAL NOT NULL,
                status TEXT NOT NULL DEFAULT 'placed',
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
            """
        )


def _row_to_order(row: sqlite3.Row) -> dict:
    return {
        "id": row["id"],
        "items": json.loads(row["items"]),
        "total": row["total"],
        "status": row["status"],
        "created_at": row["created_at"],
    }


def create_order(items: list, total: float) -> dict:
    with _connect() as conn:
        cur = conn.execute(
            "INSERT INTO orders (items, total) VALUES (?, ?)",
            (json.dumps(items), total),
        )
        order_id = cur.lastrowid
    return get_order(order_id)


def get_order(order_id: int) -> dict | None:
    with _connect() as conn:
        row = conn.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()
    return _row_to_order(row) if row else None


def cancel_order(order_id: int) -> dict | None:
    with _connect() as conn:
        conn.execute("UPDATE orders SET status = 'cancelled' WHERE id = ?", (order_id,))
    return get_order(order_id)
