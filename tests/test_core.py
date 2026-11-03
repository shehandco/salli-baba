"""Self-checks for the non-trivial logic (DB math + chatbot parsing).
No GUI here -- those paths are exercised by hand since Tkinter needs a display.
Run with: python -m pytest tests/  (or `python tests/test_core.py`)
"""
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import db
from app.chatbot import answer


def make_conn():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    db.init_db(conn)
    return conn


def test_balance_and_category_totals():
    conn = make_conn()
    db.add_transaction(conn, "income", 50000, "Other", txn_date="2026-11-01")
    db.add_transaction(conn, "expense", 1200, "Food", txn_date="2026-11-02")
    db.add_transaction(conn, "expense", 300, "Food", txn_date="2026-11-03")
    db.add_transaction(conn, "expense", 2000, "Transport", txn_date="2026-11-03")

    assert db.balance(conn) == 50000 - 1200 - 300 - 2000

    totals = db.expense_by_category(conn, "2026-11-01", "2026-11-30")
    assert totals["Food"] == 1500
    assert totals["Transport"] == 2000


def test_rejects_bad_input():
    conn = make_conn()
    try:
        db.add_transaction(conn, "expense", -5, "Food")
        assert False, "should have raised"
    except ValueError:
        pass
    try:
        db.add_transaction(conn, "savings", 5, "Food")
        assert False, "should have raised"
    except ValueError:
        pass


def test_chatbot_answers_category_question():
    conn = make_conn()
    today = __import__("datetime").date.today().isoformat()
    db.add_transaction(conn, "expense", 1500, "Food", txn_date=today)
    reply = answer(conn, "how much did I spend on food this month?")
    assert "1,500" in reply or "1500" in reply
    assert "Food" in reply


def test_chatbot_balance_question():
    conn = make_conn()
    db.add_transaction(conn, "income", 1000, "Other")
    reply = answer(conn, "what's my balance?")
    assert "1,000" in reply or "1000" in reply


if __name__ == "__main__":
    test_balance_and_category_totals()
    test_rejects_bad_input()
    test_chatbot_answers_category_question()
    test_chatbot_balance_question()
    print("All tests passed.")
