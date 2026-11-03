"""Receipt scanning: pull an amount and a date out of a photographed receipt.

Requires the Tesseract OCR engine installed on the machine (see README) --
pytesseract just calls out to it. Best-effort regex parsing: receipts are
printed in dozens of layouts, so this reads the text and takes the most
likely total/date rather than trying to understand the whole receipt.
"""
import re
from datetime import datetime

try:
    import pytesseract
    from PIL import Image
    OCR_AVAILABLE = True
except ImportError:  # Tesseract/Pillow not installed yet
    OCR_AVAILABLE = False

_AMOUNT_RE = re.compile(r"(?:rs\.?|lkr)?\s*([0-9]{1,3}(?:[,.][0-9]{3})*(?:\.[0-9]{2})?)", re.IGNORECASE)
_TOTAL_LINE_RE = re.compile(r"(total|amount|grand total|net total)", re.IGNORECASE)
_DATE_RE = re.compile(r"(\d{1,2}[/\-.]\d{1,2}[/\-.]\d{2,4})")


def _parse_amount(token: str) -> float | None:
    cleaned = token.replace(",", "")
    try:
        value = float(cleaned)
        return value if value > 0 else None
    except ValueError:
        return None


def scan_receipt(image_path: str) -> dict:
    """Returns {'amount': float|None, 'date': 'YYYY-MM-DD'|None, 'raw_text': str}."""
    if not OCR_AVAILABLE:
        return {"amount": None, "date": None, "raw_text": "",
                "error": "OCR not available: install pytesseract, Pillow, and Tesseract-OCR."}

    text = pytesseract.image_to_string(Image.open(image_path))

    amount = None
    for line in text.splitlines():
        if _TOTAL_LINE_RE.search(line):
            match = _AMOUNT_RE.search(line)
            if match:
                amount = _parse_amount(match.group(1))
                if amount:
                    break
    if amount is None:
        candidates = [m for m in _AMOUNT_RE.finditer(text)]
        amounts = [a for a in (_parse_amount(m.group(1)) for m in candidates) if a]
        if amounts:
            amount = max(amounts)

    found_date = None
    date_match = _DATE_RE.search(text)
    if date_match:
        raw = date_match.group(1).replace(".", "/").replace("-", "/")
        for fmt in ("%d/%m/%Y", "%d/%m/%y", "%m/%d/%Y", "%m/%d/%y"):
            try:
                found_date = datetime.strptime(raw, fmt).date().isoformat()
                break
            except ValueError:
                continue

    return {"amount": amount, "date": found_date, "raw_text": text}
