"""Build a PNG line chart of the gold price history (used for Telegram)."""
import datetime
import io

import matplotlib

matplotlib.use("Agg")
import matplotlib.dates as mdates  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import matplotlib.ticker  # noqa: E402

from telegram_utils import inr  # noqa: E402

MAROON = "#5B1A2E"
ZARI = "#B8892E"


def make_chart(history: dict, days: int = 30) -> bytes:
    """Return PNG bytes for the last `days` entries of history {date: price}."""
    items = sorted(history.items())[-days:]
    if not items:
        raise ValueError("No history yet")
    dates = [datetime.date.fromisoformat(d) for d, _ in items]
    prices = [p for _, p in items]

    fig, ax = plt.subplots(figsize=(9, 4.8), dpi=130)
    ax.plot(dates, prices, color=MAROON, linewidth=2.2, marker="o", markersize=3.5)
    ax.fill_between(dates, prices, min(prices) * 0.995, color=ZARI, alpha=0.18)

    hi, lo = max(prices), min(prices)
    ax.set_title(
        f"Chennai 22K gold, per gram (last {len(items)} days)\n"
        f"Latest {inr(prices[-1])}   High {inr(hi)}   Low {inr(lo)}",
        fontsize=11, color=MAROON, loc="left",
    )
    ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{inr(v)}"))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%d %b"))
    fig.autofmt_xdate()
    ax.grid(axis="y", alpha=0.3)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    fig.tight_layout()

    buf = io.BytesIO()
    fig.savefig(buf, format="png")
    plt.close(fig)
    return buf.getvalue()
