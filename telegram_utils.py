"""Small helpers for talking to the Telegram Bot API."""
import json
import os

import requests

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
# Link to your history web page, e.g. https://yourname.github.io/gold-alert/
DASHBOARD_URL = os.environ.get("DASHBOARD_URL", "").strip()

API = f"https://api.telegram.org/bot{BOT_TOKEN}"


def _history_button():
    if not DASHBOARD_URL:
        return {}
    keyboard = {"inline_keyboard": [[{"text": "📊 View full history", "url": DASHBOARD_URL}]]}
    return {"reply_markup": json.dumps(keyboard)}


def send_message(text: str, chat_id=None, with_button: bool = True) -> None:
    data = {"chat_id": chat_id or CHAT_ID, "text": text, "parse_mode": "HTML"}
    if with_button:
        data.update(_history_button())
    requests.post(f"{API}/sendMessage", data=data, timeout=30).raise_for_status()


def send_photo(png: bytes, caption: str = "", chat_id=None) -> None:
    data = {"chat_id": chat_id or CHAT_ID, "caption": caption, "parse_mode": "HTML"}
    data.update(_history_button())
    requests.post(
        f"{API}/sendPhoto", data=data, files={"photo": ("chart.png", png, "image/png")}, timeout=60
    ).raise_for_status()


def inr(n) -> str:
    """Format a number the Indian way: 119992 -> ₹1,19,992."""
    s = str(int(round(n)))
    neg = s.startswith("-")
    s = s.lstrip("-")
    if len(s) > 3:
        head, tail = s[:-3], s[-3:]
        groups = []
        while len(head) > 2:
            groups.insert(0, head[-2:])
            head = head[:-2]
        if head:
            groups.insert(0, head)
        s = ",".join(groups) + "," + tail
    return ("-" if neg else "") + "₹" + s
