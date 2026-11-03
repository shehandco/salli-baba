<p align="center">
  <img src="assets/logo.png" width="120" alt="Salli Baba logo" />
</p>

<h1 align="center">සල්ලි බබා — Salli Baba</h1>
<p align="center"><b>An AI-powered personal budget tracker for Sri Lanka, not another spreadsheet clone.</b></p>

<p align="center">Built by <b>Kepler Technologies</b></p>

---

## Why Salli Baba is different

Most budget trackers are just a form and a table. Salli Baba adds two things
that do real work for you:

- **AI receipt scanning** — point it at a photo of a receipt and it reads the
  total and date off it (OCR) and fills in the expense form for you.
- **Ask Salli (AI chatbot)** — type a plain question like *"how much did I
  spend on food this month?"* or *"what's my balance?"* and get an answer
  computed straight from your own data, instantly, with nothing sent to the
  cloud.

On top of that it has everything a Sri Lankan budget needs out of the box:
LKR (Rs.) as the default currency, a bill-payment list with due dates and
receipt attachments, and spending graphs (category breakdown + monthly
income vs. expense trend).

## Features

- Income & expense tracking with categories and notes
- Bill list with due dates, paid/unpaid status, and receipt uploads
- Dashboard with a category pie chart and a 6-month income vs. expense chart
- AI receipt scanning (OCR) to auto-fill the amount and date from a photo
- "Ask Salli" chatbot for natural-language questions about your spending
- Local-only SQLite storage — your financial data never leaves your PC
- Packaged as a single Windows `.exe` via PyInstaller

## Screenshots

_Add screenshots of the Dashboard, Add Transaction, and Ask Salli tabs here
once you've run the app._

## Tech stack

Python 3.11+, [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter)
for the UI, SQLite for storage, Matplotlib for charts, and
[Tesseract OCR](https://github.com/tesseract-ocr/tesseract) (via pytesseract)
for receipt scanning.

## Running from source

```bash
git clone https://github.com/<your-username>/salli-baba.git
cd salli-baba
pip install -r requirements.txt
python main.py
```

Receipt scanning needs the Tesseract OCR engine installed separately
(it's a system program, not a Python package):

- Windows: install from https://github.com/UB-Mannheim/tesseract/wiki and
  make sure `tesseract.exe` is on your `PATH`.
- Without it, every other feature still works — the scan button just shows
  "OCR not installed" and you enter the amount by hand.

## Building the Windows .exe

Run this on a Windows machine (PyInstaller does not cross-compile):

```bat
cd build
build.bat
```

The finished app appears at `dist/SalliBaba/SalliBaba.exe`.

## Tests

```bash
python -m pytest tests/
```

## Project layout

```
salli-baba/
  main.py              entry point
  app/
    db.py               SQLite schema + queries
    app_ui.py            CustomTkinter UI (Dashboard, Add Transaction, Bills, Ask Salli)
    chatbot.py           natural-language query engine for "Ask Salli"
    ocr_utils.py          receipt OCR parsing
    charts.py             matplotlib figures
  assets/
    logo.png / logo.ico   app logo and Windows icon
  build/
    build.spec, build.bat PyInstaller packaging
  tests/
    test_core.py           self-checks for the DB and chatbot logic
```

## License

MIT — see [LICENSE](LICENSE).

---

<p align="center">
  <a href="https://sallibaba.carrd.co/">Website</a> ·
  <a href="https://www.facebook.com/sallibabaapp">Facebook</a>
</p>
