import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from scraper import fetch_student_jobs
import asyncio
import requests
import json
from pathlib import Path
from datetime import time
from zoneinfo import ZoneInfo

PROJECT_ROOT = Path(__file__).resolve().parent.parent  # finds the folder
STATE_FILE = (
    PROJECT_ROOT / "data" / "subscriptions.json"
)  # points to the json file inside data

STATE_FILE.parent.mkdir(parents=True, exist_ok=True)


load_dotenv()

token = os.getenv("TELEGRAM_BOT_TOKEN")


if token:
    print("sucessfully read")
else:
    print("there is no token")


# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("The bot is working")


# /jobs
async def jobs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Looking for jobs...")

    # eror handling
    try:
        ads = await asyncio.to_thread(fetch_student_jobs)
    except requests.RequestException:
        await update.message.reply_text(
            "Could not fetch the jobs, please try again later"
        )
        return

    number_of_ads = len(ads)
    await update.message.reply_text(f"Found {number_of_ads} jobs")
    # send all found jobs
    for advert in ads:
        message = (
            f"Title: {advert['title']}\n"
            f"Company: {advert['company']}\n"
            f"Location: {advert['location']}\n"
            f"Pay: {advert['pay']}\n"
            f"Link: {advert['link']}"
        )
        await update.message.reply_text(message)


# /subscribe - for scheduling
async def subscribe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    #preserve history
    state = load_state()

    if state.get("chat_id") == chat_id:
        await update.message.reply_text("You already subscribed to daily alerts")
        return
    
    # eror handling
    try:
        ads = await asyncio.to_thread(fetch_student_jobs)
    except requests.RequestException:
        await update.message.reply_text(
            "Could not fetch the jobs, please try again later"
        )
        return

    # to keep track
    seen_links = []

    for advert in ads:
        seen_links.append(advert["link"])

    state = {"chat_id": chat_id, "seen_links": seen_links}
    state_text = json.dumps(state, indent=2)
    STATE_FILE.write_text(state_text, encoding="utf-8")

    await update.message.reply_text(f"Chat ID: {chat_id}")


def load_state():
    if not STATE_FILE.exists():
        return {}
    else:
        state_text = STATE_FILE.read_text(encoding="utf-8")
        state = json.loads(state_text)  # turn into dictionary
        return state


async def send_daily_jobs(context: ContextTypes.DEFAULT_TYPE):
    state = load_state()

    if not state:
        return

    chat_id = state["chat_id"]
    seen_links = set(state["seen_links"])

    try:
        ads = await asyncio.to_thread(fetch_student_jobs)
    except requests.RequestException:
        print("Could not fetch jobs.")

        return

    for advert in ads:
        link = advert["link"]

        if link in seen_links:
            continue

        print("Sending new job:", link)
        message = (
            f"Title: {advert['title']}\n"
            f"Company: {advert['company']}\n"
            f"Location: {advert['location']}\n"
            f"Pay: {advert['pay']}\n"
            f"Link: {advert['link']}"
        )
        await context.bot.send_message(chat_id=chat_id, text=message)

        seen_links.add(link)

        # save the updated history
        state["seen_links"] = list(seen_links)
        state_text = json.dumps(state, indent=2)
        STATE_FILE.write_text(state_text, encoding="utf-8")


app = Application.builder().token(token).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("jobs", jobs))
app.add_handler(CommandHandler("subscribe", subscribe))

# send daily
app.job_queue.run_daily(
    callback=send_daily_jobs,
    time=time(hour=12, minute=0, tzinfo=ZoneInfo("Europe/Ljubljana")),
)


# test
# app.job_queue.run_once(send_daily_jobs, when=10)

print("Bot is listening send  /start in Telegram.")
app.run_polling()
