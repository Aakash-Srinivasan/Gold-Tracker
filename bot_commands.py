"""
Answer Telegram commands sent to the bot:

  /today          latest saved rate
  /history        last 10 days as a list   (/history 30 for more)
  /graph          graph of the last 30 days (/graph 90, /graph 365)
  /help           list of commands

GitHub Actions runs this every 15 minutes, so replies can take a few minutes.
Only messages from your own TELEGRAM_CHAT_ID are answered.
"""
import requests

from chart import make_chart
from gold_alert import load_history
from telegram_utils import API, BOT_TOKEN, CHAT_ID, inr, send_message, send_photo

HELP = (
    "🪙 <b>Chennai gold rate bot</b>\n\n"
    "/today – latest 22K rate\n"
    "/history – last 10 days (try /history 30)\n"
    "/graph – 30-day graph (try /graph 90 or /graph 365)"
)


def arg_int(text: str, default: int, lo: int, hi: int) -> int:
    parts = text.split()
    if len(parts) > 1 and parts[1].isdigit():
        return max(lo, min(hi, int(parts[1])))
    return default


def cmd_today(history, chat_id):
    if not history:
        return send_message("No rates saved yet. The first one arrives after the daily run.", chat_id)
    date, price = sorted(history.items())[-1]
    send_message(
        f"🪙 <b>{date}</b>\n22K: <b>{inr(price)}</b>/g\nSovereign (8g): <b>{inr(price * 8)}</b>", chat_id
    )


def cmd_history(history, chat_id, n):
    items = sorted(history.items())[-n:]
    if not items:
        return send_message("No rates saved yet.", chat_id)
    lines, prev = [], None
    for date, price in items:
        if prev is None:
            change = ""
        elif price > prev:
            change = f"  ▲ {price - prev:,}"
        elif price < prev:
            change = f"  ▼ {prev - price:,}"
        else:
            change = "  –"
        lines.append(f"{date}  {inr(price)}{change}")
        prev = price
    lines.reverse()  # newest first
    send_message(f"📜 <b>Last {len(items)} days (22K per gram)</b>\n<pre>" + "\n".join(lines) + "</pre>", chat_id)


def cmd_graph(history, chat_id, days):
    if len(history) < 2:
        return send_message("Need at least 2 days of rates before a graph can be drawn.", chat_id)
    send_photo(make_chart(history, days), caption=f"📈 Chennai 22K, last {min(days, len(history))} days", chat_id=chat_id)


def main():
    if not BOT_TOKEN or not CHAT_ID:
        print("Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID.")
        return
    updates = requests.get(f"{API}/getUpdates", params={"timeout": 0}, timeout=30).json().get("result", [])
    if not updates:
        print("No new commands.")
        return

    history = load_history()
    for upd in updates:
        msg = upd.get("message") or {}
        chat_id = str(msg.get("chat", {}).get("id", ""))
        text = (msg.get("text") or "").strip()
        if chat_id != str(CHAT_ID) or not text.startswith("/"):
            continue  # ignore strangers and plain chat
        cmd = text.split()[0].split("@")[0].lower()
        try:
            if cmd == "/today":
                cmd_today(history, chat_id)
            elif cmd == "/history":
                cmd_history(history, chat_id, arg_int(text, 10, 1, 60))
            elif cmd == "/graph":
                cmd_graph(history, chat_id, arg_int(text, 30, 2, 3650))
            else:
                send_message(HELP, chat_id)
        except Exception as e:  # noqa: BLE001
            send_message(f"⚠️ Something went wrong: {e}", chat_id, with_button=False)

    # Tell Telegram these updates are handled so they aren't answered twice.
    requests.get(f"{API}/getUpdates", params={"offset": updates[-1]["update_id"] + 1, "timeout": 0}, timeout=30)


if __name__ == "__main__":
    main()
