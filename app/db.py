"""SQLite storage for Salli Baba (සල්ලි බබා).

One file, one connection helper, one table per concept. Kept deliberately
small: the app is a single-user desktop tool, not a multi-tenant service.
"""
import sqlite3
from datetime import datetime, date
from pathlib import Path

DB_PATH = Path.home() / ".salli_baba" / "salli_baba.db"

CATEGORIES = [
    "Food", "Transport", "Bills", "Shopping",
    "Entertainment", "Health", "Education", "Other",
]


def connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            kind TEXT NOT NULL CHECK(kind IN ('income', 'expense')),
            amount REAL NOT NULL CHECK(amount > 0),
            category TEXT NOT NULL,
            note TEXT DEFAULT '',
            txn_date TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS bills (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            amount REAL NOT NULL CHECK(amount > 0),
            due_date TEXT NOT NULL,
            paid INTEGER NOT NULL DEFAULT 0,
            receipt_path TEXT DEFAULT ''
        );
        """
    )
    conn.commit()


def add_transaction(conn, kind: str, amount: float, category: str,
                     note: str = "", txn_date: str | None = None) -> int:
    if kind not in ("income", "expense"):
        raise ValueError("kind must be 'income' or 'expense'")
    if amount <= 0:
        raise ValueError("amount must be positive")
    txn_date = txn_date or date.today().isoformat()
    cur = conn.execute(
        "INSERT INTO transactions (kind, amount, category, note, txn_date) "
        "VALUES (?, ?, ?, ?, ?)",
        (kind, amount, category, note, txn_date),
    )
    conn.commit()
    return cur.lastrowid


def list_transactions(conn, kind: str | None = None, limit: int = 200):
    if kind:
        rows = conn.execute(
            "SELECT * FROM transactions WHERE kind=? ORDER BY txn_date DESC, id DESC LIMIT ?",
            (kind, limit),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM transactions ORDER BY txn_date DESC, id DESC LIMIT ?",
            (limit,),
        ).fetchall()
    return rows


def delete_transaction(conn, txn_id: int) -> None:
    conn.execute("DELETE FROM transactions WHERE id=?", (txn_id,))
    conn.commit()


def add_bill(conn, name: str, amount: float, due_date: str, receipt_path: str = "") -> int:
    cur = conn.execute(
        "INSERT INTO bills (name, amount, due_date, paid, receipt_path) VALUES (?, ?, ?, 0, ?)",
        (name, amount, due_date, receipt_path),
    )
    conn.commit()
    return cur.lastrowid


def list_bills(conn, only_unpaid: bool = False):
    if only_unpaid:
        return conn.execute(
            "SELECT * FROM bills WHERE paid=0 ORDER BY due_date ASC"
        ).fetchall()
    return conn.execute("SELECT * FROM bills ORDER BY due_date ASC").fetchall()


def mark_bill_paid(conn, bill_id: int) -> None:
    conn.execute("UPDATE bills SET paid=1 WHERE id=?", (bill_id,))
    conn.commit()


def balance(conn) -> float:
    income = conn.execute(
        "SELECT COALESCE(SUM(amount), 0) FROM transactions WHERE kind='income'"
    ).fetchone()[0]
    expense = conn.execute(
        "SELECT COALESCE(SUM(amount), 0) FROM transactions WHERE kind='expense'"
    ).fetchone()[0]
    return income - expense


def expense_by_category(conn, start: str, end: str):
    """Totals per category for expenses with txn_date in [start, end]."""
    rows = conn.execute(
        "SELECT category, SUM(amount) as total FROM transactions "
        "WHERE kind='expense' AND txn_date BETWEEN ? AND ? "
        "GROUP BY category ORDER BY total DESC",
        (start, end),
    ).fetchall()
    return {row["category"]: row["total"] for row in rows}


def monthly_totals(conn, months: int = 6):
    """Last N months of (income, expense) totals, oldest first."""
    rows = conn.execute(
        "SELECT strftime('%Y-%m', txn_date) as ym, kind, SUM(amount) as total "
        "FROM transactions GROUP BY ym, kind ORDER BY ym ASC"
    ).fetchall()
    by_month: dict[str, dict[str, float]] = {}
    for row in rows:
        by_month.setdefault(row["ym"], {"income": 0.0, "expense": 0.0})
        by_month[row["ym"]][row["kind"]] = row["total"]
    ordered_keys = sorted(by_month.keys())[-months:]
    return [(k, by_month[k]["income"], by_month[k]["expense"]) for k in ordered_keys]
