"""The 'AI spending assistant'.

This is a lightweight rule-based NLP matcher, not a cloud LLM: it runs
fully offline, keeps the user's financial data on their own PC, and still
answers the questions people actually ask a budgeting app. Swap in a real
LLM API later by replacing `answer()` -- the SQL helpers in app/db.py stay
the same either way.
"""
import re
from datetime import date, timedelta
from calendar import monthrange

from app.db import CATEGORIES, expense_by_category, balance

_CATEGORY_ALIASES = {
    "food": "Food", "eating": "Food", "meal": "Food", "meals": "Food",
    "transport": "Transport", "travel": "Transport", "fuel": "Transport", "bus": "Transport",
    "bill": "Bills", "bills": "Bills", "electricity": "Bills", "water": "Bills",
    "shopping": "Shopping", "clothes": "Shopping",
    "entertainment": "Entertainment", "movie": "Entertainment", "movies": "Entertainment",
    "health": "Health", "medicine": "Health", "doctor": "Health",
    "education": "Education", "school": "Education", "tuition": "Education",
}


def _date_range(question: str) -> tuple[str, str, str]:
    """Return (start_iso, end_iso, label) for a timeframe mentioned in the question."""
    today = date.today()
    q = question.lower()
    if "today" in q:
        return today.isoformat(), today.isoformat(), "today"
    if "this week" in q:
        start = today - timedelta(days=today.weekday())
        return start.isoformat(), today.isoformat(), "this week"
    if "last month" in q:
        first_this_month = today.replace(day=1)
        last_month_end = first_this_month - timedelta(days=1)
        last_month_start = last_month_end.replace(day=1)
        return last_month_start.isoformat(), last_month_end.isoformat(), "last month"
    if "this year" in q:
        return today.replace(month=1, day=1).isoformat(), today.isoformat(), "this year"
    # default: this month
    start = today.replace(day=1)
    end = today.replace(day=monthrange(today.year, today.month)[1])
    return start.isoformat(), end.isoformat(), "this month"


def _find_category(question: str) -> str | None:
    q = question.lower()
    for alias, category in _CATEGORY_ALIASES.items():
        if alias in q:
            return category
    for category in CATEGORIES:
        if category.lower() in q:
            return category
    return None


def answer(conn, question: str) -> str:
    if not question or not question.strip():
        return "Ask me something like 'how much did I spend on food this month?'"

    q = question.lower().strip()

    if re.search(r"\b(balance|left|remaining)\b", q):
        total = balance(conn)
        return f"Your current balance is Rs. {total:,.2f}."

    if re.search(r"\b(spend|spent|spending|expense|expenses)\b", q):
        start, end, label = _date_range(q)
        category = _find_category(q)
        totals = expense_by_category(conn, start, end)
        if category:
            amount = totals.get(category, 0.0)
            return f"You spent Rs. {amount:,.2f} on {category} {label}."
        grand_total = sum(totals.values())
        if not totals:
            return f"No expenses recorded {label}."
        breakdown = ", ".join(f"{cat}: Rs. {amt:,.2f}" for cat, amt in totals.items())
        return f"You spent Rs. {grand_total:,.2f} in total {label} ({breakdown})."

    return (
        "I couldn't understand that. Try: 'how much did I spend on food this month?', "
        "'what's my balance?', or 'how much did I spend last month?'"
    )
