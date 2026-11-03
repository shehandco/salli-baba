"""CustomTkinter desktop UI for Salli Baba (සල්ලි බබා).

Four tabs: Dashboard (graphs + balance), Add Transaction (with receipt
scan), Bills, and Ask Salli (the chatbot). Kept as one UI module since the
app is small enough that splitting further would just add indirection.
"""
import shutil
from datetime import date
from pathlib import Path
from tkinter import filedialog, messagebox, PhotoImage

import customtkinter as ctk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from app import db
from app.chatbot import answer as chatbot_answer
from app.charts import category_pie_figure, monthly_trend_figure
from app.ocr_utils import scan_receipt, OCR_AVAILABLE

APP_TITLE = "සල්ලි බබා — Salli Baba"
RECEIPTS_DIR = Path.home() / ".salli_baba" / "receipts"
LOGO_PATH = Path(__file__).resolve().parent.parent / "assets" / "logo.png"

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("green")


class SalliBabaApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.conn = db.connect()
        db.init_db(self.conn)
        RECEIPTS_DIR.mkdir(parents=True, exist_ok=True)

        self.title(APP_TITLE)
        self.geometry("980x640")
        if LOGO_PATH.exists():
            try:
                self._icon_img = PhotoImage(file=str(LOGO_PATH))
                self.iconphoto(True, self._icon_img)
            except Exception:
                pass  # some platforms/Tk builds can't load PNG icons; app still runs fine

        self.tabs = ctk.CTkTabview(self)
        self.tabs.pack(fill="both", expand=True, padx=12, pady=12)
        self.tabs.add("Dashboard")
        self.tabs.add("Add Transaction")
        self.tabs.add("Bills")
        self.tabs.add("Ask Salli")

        self._build_dashboard(self.tabs.tab("Dashboard"))
        self._build_add_transaction(self.tabs.tab("Add Transaction"))
        self._build_bills(self.tabs.tab("Bills"))
        self._build_chatbot(self.tabs.tab("Ask Salli"))

    # ---------------------------------------------------------------- Dashboard
    def _build_dashboard(self, parent):
        self.balance_label = ctk.CTkLabel(parent, text="", font=("Iskoola Pota", 22, "bold"))
        self.balance_label.pack(pady=(16, 8))

        self.charts_frame = ctk.CTkFrame(parent, fg_color="transparent")
        self.charts_frame.pack(fill="both", expand=True)

        refresh_btn = ctk.CTkButton(parent, text="Refresh", command=self.refresh_dashboard)
        refresh_btn.pack(pady=8)

        self.refresh_dashboard()

    def refresh_dashboard(self):
        self.balance_label.configure(text=f"Balance: Rs. {db.balance(self.conn):,.2f}")

        for widget in self.charts_frame.winfo_children():
            widget.destroy()

        today = date.today()
        start = today.replace(day=1).isoformat()
        end = today.isoformat()
        totals = db.expense_by_category(self.conn, start, end)
        pie_fig = category_pie_figure(totals)
        pie_canvas = FigureCanvasTkAgg(pie_fig, master=self.charts_frame)
        pie_canvas.draw()
        pie_canvas.get_tk_widget().pack(side="left", fill="both", expand=True, padx=8, pady=8)

        trend_fig = monthly_trend_figure(db.monthly_totals(self.conn))
        trend_canvas = FigureCanvasTkAgg(trend_fig, master=self.charts_frame)
        trend_canvas.draw()
        trend_canvas.get_tk_widget().pack(side="left", fill="both", expand=True, padx=8, pady=8)

    # ------------------------------------------------------------ Add Transaction
    def _build_add_transaction(self, parent):
        form = ctk.CTkFrame(parent)
        form.pack(padx=16, pady=16, fill="x")

        self.kind_var = ctk.StringVar(value="expense")
        ctk.CTkLabel(form, text="Type").grid(row=0, column=0, sticky="w", padx=6, pady=6)
        ctk.CTkOptionMenu(form, values=["expense", "income"], variable=self.kind_var).grid(
            row=0, column=1, sticky="w", padx=6, pady=6
        )

        ctk.CTkLabel(form, text="Amount (Rs.)").grid(row=1, column=0, sticky="w", padx=6, pady=6)
        self.amount_entry = ctk.CTkEntry(form, width=200)
        self.amount_entry.grid(row=1, column=1, sticky="w", padx=6, pady=6)

        ctk.CTkLabel(form, text="Category").grid(row=2, column=0, sticky="w", padx=6, pady=6)
        self.category_var = ctk.StringVar(value=db.CATEGORIES[0])
        ctk.CTkOptionMenu(form, values=db.CATEGORIES, variable=self.category_var).grid(
            row=2, column=1, sticky="w", padx=6, pady=6
        )

        ctk.CTkLabel(form, text="Note").grid(row=3, column=0, sticky="w", padx=6, pady=6)
        self.note_entry = ctk.CTkEntry(form, width=300)
        self.note_entry.grid(row=3, column=1, sticky="w", padx=6, pady=6)

        self.scanned_receipt_path = None
        scan_btn = ctk.CTkButton(form, text="Scan receipt (AI)", command=self._on_scan_receipt)
        scan_btn.grid(row=4, column=0, sticky="w", padx=6, pady=6)
        self.scan_status = ctk.CTkLabel(form, text="" if OCR_AVAILABLE else "OCR not installed (see README)")
        self.scan_status.grid(row=4, column=1, sticky="w", padx=6, pady=6)

        save_btn = ctk.CTkButton(form, text="Save", command=self._on_save_transaction)
        save_btn.grid(row=5, column=0, columnspan=2, pady=12)

    def _on_scan_receipt(self):
        path = filedialog.askopenfilename(
            title="Select receipt photo",
            filetypes=[("Images", "*.png *.jpg *.jpeg")],
        )
        if not path:
            return
        result = scan_receipt(path)
        if result.get("error"):
            messagebox.showwarning("Receipt scan", result["error"])
            return
        if result["amount"]:
            self.amount_entry.delete(0, "end")
            self.amount_entry.insert(0, f"{result['amount']:.2f}")
        self.scanned_receipt_path = path
        found = []
        if result["amount"]:
            found.append(f"Rs. {result['amount']:.2f}")
        if result["date"]:
            found.append(result["date"])
        self.scan_status.configure(text="Found: " + ", ".join(found) if found else "No amount found, enter manually")

    def _on_save_transaction(self):
        try:
            amount = float(self.amount_entry.get())
        except ValueError:
            messagebox.showerror("Invalid amount", "Enter a valid number for amount.")
            return
        try:
            db.add_transaction(
                self.conn,
                kind=self.kind_var.get(),
                amount=amount,
                category=self.category_var.get(),
                note=self.note_entry.get(),
            )
        except ValueError as exc:
            messagebox.showerror("Could not save", str(exc))
            return

        if self.scanned_receipt_path:
            dest = RECEIPTS_DIR / f"{date.today().isoformat()}_{Path(self.scanned_receipt_path).name}"
            shutil.copy(self.scanned_receipt_path, dest)
            self.scanned_receipt_path = None

        self.amount_entry.delete(0, "end")
        self.note_entry.delete(0, "end")
        self.scan_status.configure(text="")
        messagebox.showinfo("Saved", "Transaction saved.")
        self.refresh_dashboard()

    # ------------------------------------------------------------------- Bills
    def _build_bills(self, parent):
        form = ctk.CTkFrame(parent)
        form.pack(padx=16, pady=16, fill="x")

        ctk.CTkLabel(form, text="Bill name").grid(row=0, column=0, padx=6, pady=6, sticky="w")
        self.bill_name_entry = ctk.CTkEntry(form, width=200)
        self.bill_name_entry.grid(row=0, column=1, padx=6, pady=6, sticky="w")

        ctk.CTkLabel(form, text="Amount (Rs.)").grid(row=1, column=0, padx=6, pady=6, sticky="w")
        self.bill_amount_entry = ctk.CTkEntry(form, width=200)
        self.bill_amount_entry.grid(row=1, column=1, padx=6, pady=6, sticky="w")

        ctk.CTkLabel(form, text="Due date (YYYY-MM-DD)").grid(row=2, column=0, padx=6, pady=6, sticky="w")
        self.bill_due_entry = ctk.CTkEntry(form, width=200)
        self.bill_due_entry.insert(0, date.today().isoformat())
        self.bill_due_entry.grid(row=2, column=1, padx=6, pady=6, sticky="w")

        add_btn = ctk.CTkButton(form, text="Add bill", command=self._on_add_bill)
        add_btn.grid(row=3, column=0, columnspan=2, pady=10)

        self.bills_list_frame = ctk.CTkScrollableFrame(parent, label_text="Upcoming bills")
        self.bills_list_frame.pack(fill="both", expand=True, padx=16, pady=(0, 16))
        self._refresh_bills_list()

    def _on_add_bill(self):
        try:
            amount = float(self.bill_amount_entry.get())
        except ValueError:
            messagebox.showerror("Invalid amount", "Enter a valid number for amount.")
            return
        name = self.bill_name_entry.get().strip()
        due = self.bill_due_entry.get().strip()
        if not name or not due:
            messagebox.showerror("Missing info", "Enter a bill name and due date.")
            return
        db.add_bill(self.conn, name, amount, due)
        self.bill_name_entry.delete(0, "end")
        self.bill_amount_entry.delete(0, "end")
        self._refresh_bills_list()

    def _refresh_bills_list(self):
        for widget in self.bills_list_frame.winfo_children():
            widget.destroy()
        for bill in db.list_bills(self.conn):
            row = ctk.CTkFrame(self.bills_list_frame, fg_color="transparent")
            row.pack(fill="x", pady=2)
            status = "Paid" if bill["paid"] else "Due"
            text = f"{bill['due_date']} — {bill['name']} — Rs. {bill['amount']:,.2f} [{status}]"
            ctk.CTkLabel(row, text=text).pack(side="left", padx=4)
            if not bill["paid"]:
                ctk.CTkButton(
                    row, text="Mark paid", width=90,
                    command=lambda b=bill["id"]: self._mark_paid(b),
                ).pack(side="right", padx=4)

    def _mark_paid(self, bill_id):
        db.mark_bill_paid(self.conn, bill_id)
        self._refresh_bills_list()

    # ---------------------------------------------------------------- Ask Salli
    def _build_chatbot(self, parent):
        intro = ctk.CTkLabel(
            parent,
            text="Ask things like: \"how much did I spend on food this month?\" or \"what's my balance?\"",
            wraplength=700,
        )
        intro.pack(pady=(16, 8))

        self.chat_log = ctk.CTkTextbox(parent, height=380)
        self.chat_log.pack(fill="both", expand=True, padx=16, pady=8)
        self.chat_log.configure(state="disabled")

        input_row = ctk.CTkFrame(parent, fg_color="transparent")
        input_row.pack(fill="x", padx=16, pady=(0, 16))
        self.chat_entry = ctk.CTkEntry(input_row)
        self.chat_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.chat_entry.bind("<Return>", lambda _e: self._on_ask())
        ctk.CTkButton(input_row, text="Ask", command=self._on_ask).pack(side="right")

    def _on_ask(self):
        question = self.chat_entry.get().strip()
        if not question:
            return
        reply = chatbot_answer(self.conn, question)
        self.chat_log.configure(state="normal")
        self.chat_log.insert("end", f"You: {question}\nSalli: {reply}\n\n")
        self.chat_log.configure(state="disabled")
        self.chat_log.see("end")
        self.chat_entry.delete(0, "end")


def run():
    app = SalliBabaApp()
    app.mainloop()
