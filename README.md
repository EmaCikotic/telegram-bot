# Telegram Job Bot

A personal Python bot that finds student IT jobs on e-Študentski Servis and sends them through Telegram.

## Features

- `/start` — check that the bot works
- `/jobs` — fetch matching jobs across result pages
- `/subscribe` — enable local daily alerts
- `/unsubscribe` — pause local alerts without losing history
- Send only unseen listings in daily alerts
- Restrict commands to the owner

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

Keep `.env` and generated history files out of Git.

## Run locally

Start the interactive bot:

```bash
python src/bot.py
```

Run one job-alert check:

```bash
python src/daily_jobs.py
```

The first daily-script run saves current listings without sending them. Later runs send new listings.

## GitHub Actions

Daily alerts run automatically through GitHub Actions, scheduled for **12:00 Ljubljana time**. Your computer can be off. GitHub may delay scheduled runs, so messages might arrive after noon.

Interactive commands such as `/jobs` require `bot.py` to be running locally.

Add these repository secrets:

- `TELEGRAM_BOT_TOKEN`
- `OWNER_USER_ID`
- `TELEGRAM_CHAT_ID`

To run a check manually, open **Actions → Daily job alerts → Run workflow**.

Job history is saved between runs as an artifact containing only job links. Messages are sent only when new listings are found.

To pause deployed alerts, disable the workflow on GitHub. Local `/unsubscribe` does not pause GitHub alerts.



## Planned

- More job sources
- Move scheduling and hosting to another service
