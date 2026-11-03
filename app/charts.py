"""Matplotlib figures for the dashboard, built from plain dicts/lists so
they're easy to unit-test without touching Tkinter."""
import matplotlib
matplotlib.use("Agg")  # overridden to TkAgg by app_ui at import time when a display exists
import matplotlib.pyplot as plt


def category_pie_figure(totals: dict):
    fig, ax = plt.subplots(figsize=(4, 4))
    if not totals:
        ax.text(0.5, 0.5, "No expenses yet", ha="center", va="center")
        ax.axis("off")
        return fig
    ax.pie(totals.values(), labels=totals.keys(), autopct="%1.0f%%", startangle=90)
    ax.set_title("Expenses by category")
    return fig


def monthly_trend_figure(monthly_rows):
    fig, ax = plt.subplots(figsize=(5, 3))
    if not monthly_rows:
        ax.text(0.5, 0.5, "No data yet", ha="center", va="center")
        ax.axis("off")
        return fig
    months = [row[0] for row in monthly_rows]
    income = [row[1] for row in monthly_rows]
    expense = [row[2] for row in monthly_rows]
    x = range(len(months))
    ax.bar([i - 0.2 for i in x], income, width=0.4, label="Income", color="#2e7d32")
    ax.bar([i + 0.2 for i in x], expense, width=0.4, label="Expense", color="#c62828")
    ax.set_xticks(list(x))
    ax.set_xticklabels(months, rotation=45, ha="right")
    ax.set_ylabel("Rs.")
    ax.set_title("Income vs. Expense")
    ax.legend()
    fig.tight_layout()
    return fig
