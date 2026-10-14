# Telegram Job Bot

A personal Python bot that finds student jobs on e-Študentski Servis and sends them through Telegram. The default search targets IT jobs.

## Features

- `/start` — check that the bot works
- `/jobs` — fetch matching jobs across result pages
- `/subscribe` — enable local daily alerts
- `/unsubscribe` — pause local alerts without losing history
- Editable pay, location, and category filters
- Send only unseen listings in daily alerts
- Restrict commands to the owner

## Search filters

- `/settings` — show current filters
- `/minpay 10` — set minimum net hourly pay
- `/maxpay 20` — set maximum net hourly pay
- `/location obala` — choose an area
- `/location all` — search all locations
- `/categories` — choose a category or subcategory using Slovenian buttons
- `/resetfilters` — restore defaults

Settings are saved locally and survive restarts. `/jobs` uses the saved filters.

Category selection replaces the previous selection. You can choose one whole group or one subcategory at a time.

Daily alerts currently use the original default filters. Local filter changes do not update GitHub alerts.

## Project structure

```text
telegram-bot/
├── .github/
│   └── workflows/
│       └── daily-jobs.yml     # GitHub Actions workflow
├── data/                     # Local files excluded from Git
│   ├── subscriptions.json    # Subscription and job history
│   ├── job-history.json      # History used by the daily script
│   └── filters.json          # Saved search preferences
├── src/
│   ├── bot.py                # Bot startup, subscriptions, and job sending
│   ├── access.py             # Owner checks
│   ├── categories.py         # Slovenian category catalogue
│   ├── category_handlers.py  # Category buttons and selection
│   ├── filter_handlers.py    # Settings and filter commands
│   ├── filter_storage.py     # Load and save filters
│   ├── locations.py          # Location options
│   ├── scraper.py            # Search URL builder and job scraper
│   ├── daily_jobs.py         # Standalone daily runner
│   └── extract_categories.py # Refresh the category catalogue
├── .env                      # Local credentials, excluded from Git
├── .gitignore
├── requirements.txt
└── README.md
```

Files in `data/` are created as needed.

## Setup

Install dependencies:

```bash
pip install -r requirements.txt
```

Create a `.env` file:

```text
TELEGRAM_BOT_TOKEN=your_token
OWNER_USER_ID=your_user_id
TELEGRAM_CHAT_ID=your_chat_id
```

Keep `.env` and generated history/settings files out of Git.

## Run locally

Start the interactive bot:

```bash
python src/bot.py
```

Run one job-alert check:

```bash
python src/daily_jobs.py
```

The first daily-script run saves current listings without sending them. Later runs send new listings, or a confirmation when no new jobs are found.

## Daily alerts

cron-job.org starts the GitHub Actions workflow every day at **12:00 Ljubljana time**. Your computer can be off, although messages may arrive later than scheduled.

The setup has successfully triggered a workflow and delivered a Telegram message. Automatic daily execution still needs to be confirmed.

Each run checks for new listings and saves job history for future runs. If no new jobs are found, the bot sends a confirmation.

Configure these repository secrets on GitHub:

- `TELEGRAM_BOT_TOKEN`
- `OWNER_USER_ID`
- `TELEGRAM_CHAT_ID`

For a manual check, select **Actions → Daily job alerts → Run workflow**.

Telegram commands require `bot.py` to be running locally. Saved local filters are not yet shared with GitHub alerts.

## Planned

- Verify automatic scheduling
- Apply saved filters to daily alerts
- Add per-user settings and subscriptions
- Add more job sources
- Move scheduling and hosting to another service
