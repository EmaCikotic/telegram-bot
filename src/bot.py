import math
import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from scraper import fetch_student_jobs, default_filters, build_search_url
import asyncio
import requests
import json
from pathlib import Path
from datetime import time
from zoneinfo import ZoneInfo
from telegram.error import TelegramError
import copy

PROJECT_ROOT = Path(__file__).resolve().parent.parent  # finds the folder
STATE_FILE = (
    PROJECT_ROOT / "data" / "subscriptions.json"
)  # points to the json file inside data

FILTERS_FILE = PROJECT_ROOT / "data" / "filters.json"

STATE_FILE.parent.mkdir(parents=True, exist_ok=True)


load_dotenv()

token = os.getenv("TELEGRAM_BOT_TOKEN")
owner_user_id = os.getenv("OWNER_USER_ID")


if token:
    print("sucessfully read")
else:
    raise SystemExit("Missing TELEGRAM_BOT_TOKEN. Add it to your .env file.")

if owner_user_id:
    print("sucessfully read")
else:
    raise SystemExit("Missing OWNER_USER_ID. Add it to your .env file.")

owner_user_id = int(owner_user_id)


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


def save_filters(filters):
    filter_json = json.dumps(filters, indent=2)

    FILTERS_FILE.write_text(filter_json, encoding="utf-8")


def is_owner(update):
    return update.effective_user.id == owner_user_id


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


# /settings
async def settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update):
        await update.message.reply_text("This is a personal bot")
        return

    filters = load_filters()

    regions = filters["regions"]
    location_text = ", ".join(regions) if regions else "All locations"
    category_text = ", ".join(filters["categories"])

    message = (
        f"Locations: {location_text}\n"
        f"Category codes: {category_text}\n"
        f"Minimum pay: €{filters['min_pay']}/hour\n"
        f"Maximum pay: €{filters['max_pay']}/hour\n"
    )
    await update.message.reply_text(message)


# /minpay update
async def minpay(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update):
        await update.message.reply_text("This is a personal bot")
        return

    if len(context.args) != 1:
        await update.message.reply_text("Usage: /minpay 10")
        return

    try:
        min_pay = float(context.args[0])
    except ValueError:
        await update.message.reply_text("Enter a number, for example: /minpay 10")
        return

    filters = load_filters()

    if min_pay < 0 or min_pay > filters["max_pay"] or not math.isfinite(min_pay):
        await update.message.reply_text(
            f"The minmum hourly wage has to be a finite number between zero and the current maximum:{filters['max_pay']}"
        )
        return

    # update the min pay
    filters["min_pay"] = min_pay
    save_filters(filters)  # updated dictionary

    await update.message.reply_text(f"Minimum pay set to €{min_pay:g}/hour (net).")


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


def load_filters():
    if not FILTERS_FILE.exists():
        return copy.deepcopy(default_filters)
    else:
        filters_text = FILTERS_FILE.read_text(encoding="utf-8")

        try:
            filters = json.loads(filters_text)  # turn into dictionary
        except json.JSONDecodeError:
            raise RuntimeError(
                "Filters file contains invalid JSON. Fix it before continuing"
            )

    return filters


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

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("jobs", jobs))
    app.add_handler(CommandHandler("subscribe", subscribe))
    app.add_handler(CommandHandler("unsubscribe", unsubscribe))
    app.add_handler(CommandHandler("settings", settings))
    app.add_handler(CommandHandler("minpay", minpay))

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
