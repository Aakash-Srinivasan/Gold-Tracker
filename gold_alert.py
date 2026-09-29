"""
Daily Chennai 22K gold rate -> Telegram notifier.

Env vars required:
  TELEGRAM_BOT_TOKEN  - token from @BotFather
  TELEGRAM_CHAT_ID    - your chat id
"""
import datetime
import json
import os
import re
import sys

import requests
from bs4 import BeautifulSoup

from chart import make_chart
from telegram_utils import BOT_TOKEN, CHAT_ID, inr, send_message, send_photo

# Send a 30-day graph along with the daily message on this weekday (0=Mon ... 6=Sun).
# Set WEEKLY_GRAPH_DAY=-1 to turn it off, or DAILY_GRAPH=1 to get a graph every day.
WEEKLY_GRAPH_DAY = int(os.environ.get("WEEKLY_GRAPH_DAY", "6"))
DAILY_GRAPH = os.environ.get("DAILY_GRAPH", "0") == "1"
HISTORY_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "price_history.json")

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    ),
    "Accept-Language": "en-IN,en;q=0.9",
}

# Sources are tried in order; if one fails or its layout changes, the next is used.
SOURCES = [
    {
        "name": "GoodReturns",
        "url": "https://www.goodreturns.in/gold-rates/chennai.html",
        "patterns": [
            r"22K\s*Gold\s*/\s*g\s*₹\s*([\d,]+)",
            r"22\s*Carat\s*Gold\s*Rate\s*Per\s*Gram.{0,200}?\b1\s*(?:gram|g)?\s*₹\s*([\d,]+)",
            r"22\s*(?:K|Carat)[^₹]{0,80}₹\s*([\d,]+)",
        ],
    },
    {
        "name": "BankBazaar",
        "url": "https://www.bankbazaar.com/gold-rate-chennai.html",
        "patterns": [
            r"22\s*(?:K|Carat)[^₹]{0,120}₹\s*([\d,]+)",
        ],
    },
]

# Sanity range for price per gram (INR) so we never report garbage numbers.
MIN_PRICE, MAX_PRICE = 3000, 60000


IST = datetime.timezone(datetime.timedelta(hours=5, minutes=30))


def ist_now() -> datetime.datetime:
    return datetime.datetime.now(IST)


def ist_today() -> str:
    return ist_now().strftime("%Y-%m-%d")


def fetch_rate():
    """Return (price_per_gram, source_name) or raise RuntimeError."""
    errors = []
    for src in SOURCES:
        try:
            resp = requests.get(src["url"], headers=HEADERS, timeout=30)
            resp.raise_for_status()
            text = BeautifulSoup(resp.text, "html.parser").get_text(" ", strip=True)
            for pat in src["patterns"]:
                for m in re.finditer(pat, text, flags=re.IGNORECASE | re.DOTALL):
                    price = int(m.group(1).replace(",", ""))
                    if MIN_PRICE <= price <= MAX_PRICE:
                        return price, src["name"]
            errors.append(f"{src['name']}: price not found on page")
        except Exception as e:  # noqa: BLE001
            errors.append(f"{src['name']}: {e}")
    raise RuntimeError("; ".join(errors))


def load_history() -> dict:
    try:
        with open(HISTORY_FILE, encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save_history(history: dict) -> None:
    # Full history is kept (one small line per day), sorted by date.
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(dict(sorted(history.items())), f, indent=2)


def build_message(price: int, source: str, history: dict, today: str) -> str:
    previous = [(d, p) for d, p in sorted(history.items()) if d < today]
    change_line = ""
    if previous:
        prev_date, prev_price = previous[-1]
        diff = price - prev_price
        if diff > 0:
            change_line = f"\n📈 Up {inr(diff)} from {prev_date} ({inr(prev_price)})"
        elif diff < 0:
            change_line = f"\n📉 Down {inr(abs(diff))} from {prev_date} ({inr(prev_price)})"
        else:
            change_line = f"\n➖ No change from {prev_date}"

    return (
        f"🪙 <b>Chennai Gold Rate – {today}</b>\n\n"
        f"22K (1 gram): <b>{inr(price)}</b>\n"
        f"22K (8 grams / 1 sovereign): <b>{inr(price * 8)}</b>"
        f"{change_line}\n\n"
        f"<i>Source: {source}</i>"
    )


def main() -> int:
    if not BOT_TOKEN or not CHAT_ID:
        print("Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID environment variables.")
        return 1

    today = ist_today()
    try:
        price, source = fetch_rate()
    except RuntimeError as e:
        print("Fetch failed:", e)
        send_message(f"⚠️ Could not fetch Chennai 22K gold rate today ({today}).\n{e}")
        return 1

    history = load_history()
    message = build_message(price, source, history, today)
    history[today] = price
    save_history(history)

    want_graph = DAILY_GRAPH or ist_now().weekday() == WEEKLY_GRAPH_DAY
    if want_graph and len(history) >= 2:
        send_photo(make_chart(history, days=30), caption=message)
    else:
        send_message(message)
    print(message)
    return 0


if __name__ == "__main__":
    sys.exit(main())
