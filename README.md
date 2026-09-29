# 🪎 Chennai 22K Gold Rate → Telegram (daily) + history & graph

What you get:
- **Every day at 10:00 AM IST** a Telegram message with the 22K rate per gram and per
  sovereign, and how much it moved since yesterday.
- **Every Sunday** the message comes with a 30-day graph image.
- **A "📊 View full history" button** under each message that opens your history page
  (chart with 7 days / 30 days / 90 days / 1 year / All, per gram or per sovereign,
  plus a table of every day's rate).
- **Bot commands** you can send any time:
  - `/today` latest rate
  - `/history` last 10 days (`/history 30` for more)
  - `/graph` 30-day graph (`/graph 90`, `/graph 365`)
  Replies arrive within about 15 minutes (GitHub checks for commands every 15 min).

## Files
| File | What it does |
|---|---|
| `gold_alert.py` | Fetches today's rate, saves it, sends the daily message |
| `bot_commands.py` | Answers /today, /history, /graph |
| `chart.py` | Draws the graph image for Telegram |
| `telegram_utils.py` | Sends messages/photos to Telegram |
| `index.html` | The history web page (chart + table) |
| `price_history.json` | Created automatically; one line per day |
| `.github/workflows/` | The two schedules (daily + every 15 min) |

## Setup

### 1. Telegram bot
1. In Telegram, open **@BotFather** → `/newbot` → copy the **bot token**.
2. Send "hi" to your new bot, then open
   `https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates` and copy the number in
   `"chat":{"id": ...}` — that's your **chat ID**.
3. Optional, for a command menu: in @BotFather send `/setcommands`, pick your bot, and paste:
   ```
   today - Latest 22K rate
   history - Last 10 days of rates
   graph - 30-day price graph
   ```

### 2. GitHub repository
1. Create a **public** repository (needed for the free history web page — only gold
   prices are visible; your bot token stays hidden in Secrets) and upload all files,
   keeping the `.github/workflows/` folder.
2. **Settings → Secrets and variables → Actions → Secrets** tab, add:
   - `TELEGRAM_BOT_TOKEN`
   - `TELEGRAM_CHAT_ID`

### 3. History web page (GitHub Pages)
1. **Settings → Pages** → Source: *Deploy from a branch* → Branch: `main`, folder `/ (root)` → Save.
2. After a minute your page is at `https://<your-username>.github.io/<repo-name>/`.
3. **Settings → Secrets and variables → Actions → Variables** tab, add
   `DASHBOARD_URL` = that link. This makes the "📊 View full history" button appear.

### 4. Test
**Actions** tab → "Daily Chennai Gold Rate" → **Run workflow**. You should get the
Telegram message within a minute, and the history page will show the first day.
The graph appears once there are at least 2 days of data.

## Options
- Change the daily time: edit `cron` in `daily-gold-rate.yml` (UTC; IST = UTC + 5:30).
- Graph every day instead of weekly: add a repository variable `DAILY_GRAPH` = `1` and
  pass it in the workflow `env` (same way as `DASHBOARD_URL`).
- Different weekly graph day: `WEEKLY_GRAPH_DAY` (0 = Monday … 6 = Sunday, -1 = off).

## If something stops working
- "⚠️ Could not fetch" in Telegram → the rate website changed its layout; the regex
  patterns in `SOURCES` in `gold_alert.py` need an update.
- Commands not answered → check the "Answer Telegram commands" workflow in the Actions tab.
- History page says it can't load data → wait for the first daily run to create
  `price_history.json`.
