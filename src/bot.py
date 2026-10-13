import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
)
from scraper import fetch_student_jobs, default_filters, build_search_url
import asyncio
import requests
import json
from pathlib import Path
from datetime import time
from zoneinfo import ZoneInfo
from telegram.error import TelegramError
from categories import category_groups
from access import is_owner
from filter_storage import load_filters
from category_handlers import categories, category_callback, select_category
from locations import location_options
from filter_handlers import settings, minpay, maxpay, location, resetfilters


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
    raise SystemExit("Missing TELEGRAM_BOT_TOKEN. Add it to your .env file.")


# helper functions
def format_job(advert):
    message = (
        f"Title: {advert['title']}\n"
        f"Company: {advert['company']}\n"
        f"Location: {advert['location']}\n"
        f"Pay: {advert['pay']}\n"
        f"Link: {advert['link']}"
    )
    return message


def save_state(state):
    state_text = json.dumps(state, indent=2)
    STATE_FILE.write_text(state_text, encoding="utf-8")


# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update):
        await update.message.reply_text("This is a personal bot")
        return

    await update.message.reply_text("The bot is working")


# /jobs
async def jobs(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not is_owner(update):
        await update.message.reply_text("This is a personal bot")
        return

    await update.message.reply_text("Looking for jobs...")

    filters = load_filters()
    search_url = build_search_url(filters)

    # eror handling
    try:
        ads = await asyncio.to_thread(fetch_student_jobs, search_url)
    except requests.RequestException:
        await update.message.reply_text(
            "Could not fetch the jobs, please try again later"
        )
        return

    number_of_ads = len(ads)
    await update.message.reply_text(f"Found {number_of_ads} jobs")
    # send all found jobs
    for advert in ads:
        message = format_job(advert)
        await update.message.reply_text(message)


# /subscribe - for scheduling
async def subscribe(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not is_owner(update):
        await update.message.reply_text("This is a personal bot")
        return

    chat_id = update.effective_chat.id

    # preserve history
    state = load_state()

    if state.get("chat_id") == chat_id:
        if state.get("enabled", True):
            await update.message.reply_text("You're already subscribed.")
            return

        state["enabled"] = True
        save_state(state)
        await update.message.reply_text("Daily alerts are enabled.")
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

    state = {"chat_id": chat_id, "seen_links": seen_links, "enabled": True}
    save_state(state)

    await update.message.reply_text(f"Chat ID: {chat_id}")


# /unsubscribe
async def unsubscribe(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not is_owner(update):
        await update.message.reply_text("This is a personal bot")
        return

    chat_id = update.effective_chat.id
    state = load_state()

    if state.get("chat_id") != chat_id:
        await update.message.reply_text("You are not subscribed")
        return

    state["enabled"] = False
    save_state(state)
    await update.message.reply_text("Daily alerts are disabled")


def load_state():
    if not STATE_FILE.exists():
        return {}
    else:
        state_text = STATE_FILE.read_text(encoding="utf-8")

        try:
            state = json.loads(state_text)  # turn into dictionary
        except json.JSONDecodeError:
            raise RuntimeError(
                "Subscription file contains invalid JSON. Fix it before continuing"
            )

    return state


async def send_new_jobs(bot):
    state = load_state()

    if not state:
        return

    if not state.get("enabled", True):
        return

    chat_id = state["chat_id"]
    seen_links = set(state["seen_links"])

    try:
        ads = await asyncio.to_thread(fetch_student_jobs)
    except requests.RequestException:
        print("Could not fetch jobs.")

        return

    new_jobs_count = 0

    for advert in ads:
        link = advert["link"]

        if link in seen_links:
            continue

        new_jobs_count += 1

        print("Sending new job:", link)
        message = format_job(advert)

        try:
            await bot.send_message(chat_id=chat_id, text=message)
        except TelegramError as error:
            print(f"the failed link: {link}, error: {error}")
            continue

        seen_links.add(link)

        # save the updated history
        state["seen_links"] = list(seen_links)
        save_state(state)

    if new_jobs_count == 0:
        await bot.send_message(
            chat_id=chat_id, text="Daily check complete: no new jobs found."
        )


async def send_daily_jobs(context: ContextTypes.DEFAULT_TYPE):
    await send_new_jobs(context.bot)


def main():

    app = Application.builder().token(token).build()

    # commands for the bot

    # basic commands
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("jobs", jobs))
    app.add_handler(CommandHandler("subscribe", subscribe))
    app.add_handler(CommandHandler("unsubscribe", unsubscribe))

    # filtering
    app.add_handler(CommandHandler("settings", settings))
    app.add_handler(CommandHandler("minpay", minpay))
    app.add_handler(CommandHandler("maxpay", maxpay))
    app.add_handler(CommandHandler("resetfilters", resetfilters))
    app.add_handler(CommandHandler("location", location))
    app.add_handler(CommandHandler("categories", categories))
    app.add_handler(
        CallbackQueryHandler(
            category_callback,
            pattern=r"^(category:\d+|category_back)$",
        )
    )
    app.add_handler(
        CallbackQueryHandler(
            select_category,
            pattern=r"^select_category:\d+(?::A\d+)?$",
        )
    )

    # send daily
    app.job_queue.run_daily(
        callback=send_daily_jobs,
        time=time(hour=12, minute=0, tzinfo=ZoneInfo("Europe/Ljubljana")),
    )

    # test
    # app.job_queue.run_once(send_daily_jobs, when=10)

    print("Bot is listening send  /start in Telegram.")
    app.run_polling()


if __name__ == "__main__":
    main()
