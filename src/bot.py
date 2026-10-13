import math
import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    Application,
    CallbackContext,
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
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import TelegramError
import copy
from categories import category_groups

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


location_options = {
    "all": [],
    "ljubljana": ["ljubljana-z-okolico"],
    "osrednjeslovenska": [
        "osrednjeslovenska",
        "ljubljana-z-okolico",
        "domzale-kamnik",
        "grosuplje-z-okolico",
        "vrhnika-z-okolico",
    ],
    "podravska": [
        "podravska",
        "maribor-z-okolico",
        "ptuj-z-okolico",
    ],
    "koroska": ["koroska"],
    "pomurska": ["pomurska"],
    "savinjska": ["savinjska"],
    "zasavska": ["zasavska"],
    "gorenjska": [
        "gorenjska",
        "kranj-z-okolico",
        "skofja-loka-z-okolico",
        "radovljica-z-okolico",
        "jesenice-z-okolico",
    ],
    "goriska": ["goriska"],
    "primorsko-notranjska": ["primorsko-notranjska"],
    "obala": [
        "koper-z-okolico",
        "izola-z-okolico",
        "piran-z-okolico",
    ],
    "obalno-kraska": [
        "obalno-kraska",
        "koper-z-okolico",
        "izola-z-okolico",
        "piran-z-okolico",
        "kras",
    ],
    "posavska": ["posavska"],
    "dolenjska": ["dolenjska"],
}


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


# /maxpay update
async def maxpay(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update):
        await update.message.reply_text("This is a personal bot")
        return

    if len(context.args) != 1:
        await update.message.reply_text("Usage: /maxpay 20")
        return

    try:
        max_pay = float(context.args[0])
    except ValueError:
        await update.message.reply_text("Enter a number, for example: /maxpay 100")
        return

    filters = load_filters()

    if max_pay < 0 or max_pay < filters["min_pay"] or not math.isfinite(max_pay):
        await update.message.reply_text(
            f"The maximum must be finite and at least the current minimum: {filters['min_pay']}"
        )
        return

    # update the min pay
    filters["max_pay"] = max_pay
    save_filters(filters)  # updated dictionary

    await update.message.reply_text(f"Maximal pay set to €{max_pay:g}/hour (net).")


# /location update
async def location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update):
        await update.message.reply_text("This is a personal bot.")
        return

    choices = ", ".join(location_options)

    if len(context.args) != 1:
        await update.message.reply_text(
            f"Usage: /location <area>\nAvailable: {choices}"
        )
        return

    choice = context.args[0].lower()

    if choice not in location_options:
        await update.message.reply_text(f"Unknown location.\nAvailable: {choices}")
        return

    filters = load_filters()
    filters["regions"] = location_options[choice].copy()
    save_filters(filters)

    await update.message.reply_text(f"Location set to: {choice}. Use /jobs to search.")


# /categories update
async def categories(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update):
        await update.message.reply_text("This is a personal bot.")
        return

    keyboard = []

    for code, group in category_groups.items():
        button = InlineKeyboardButton(
            text=group["name"],
            callback_data=f"category:{code}",
        )
        keyboard.append([button])

    markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "Izberi kategorijo dela:",
        reply_markup=markup,
    )


async def category_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query

    if not is_owner(update):
        await query.answer("This is a personal bot.", show_alert=True)
        return

    await query.answer()

    if query.data == "category_back":
        keyboard = [
            [
                InlineKeyboardButton(
                    text=group["name"],
                    callback_data=f"category:{code}",
                )
            ]
            for code, group in category_groups.items()
        ]

        await query.edit_message_text(
            "Izberi kategorijo dela:",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
        return

    code = query.data.split(":", 1)[1]
    group = category_groups.get(code)

    if group is None:
        await query.edit_message_text(
            "Kategorija ni več na voljo. Uporabi /categories."
        )
        return

    keyboard = [
        [
            InlineKeyboardButton(
                text="Izberi celotno kategorijo",
                callback_data=f"select_category:{code}",
            )
        ]
    ]

    for child_code, child_name in group["children"].items():
        keyboard.append(
            [
                InlineKeyboardButton(
                    text=child_name,
                    callback_data=f"select_category:{code}:{child_code}",
                )
            ]
        )

    keyboard.append([InlineKeyboardButton(text="Nazaj", callback_data="category_back")])

    await query.edit_message_text(
        f"Izberi podkategorijo: {group['name']}",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def select_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query

    if not is_owner(update):
        await query.answer("This is a personal bot.", show_alert=True)
        return

    parts = query.data.split(":")
    group_code = parts[1]
    group = category_groups.get(group_code)

    if group is None:
        await query.answer("Neveljavna kategorija.", show_alert=True)
        return

    if len(parts) == 3:
        child_code = parts[2]

        if child_code not in group["children"]:
            await query.answer("Neveljavna podkategorija.", show_alert=True)
            return

        selected_codes = [child_code]
        selected_name = group["children"][child_code]
    else:
        selected_codes = [group_code, *group["children"]]
        selected_name = group["name"]

    await query.answer()

    filters = load_filters()
    filters["categories"] = selected_codes
    save_filters(filters)

    await query.edit_message_text(
        f"Shranjena izbira: {selected_name}\nZa iskanje uporabi /jobs.",
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        text="Nazaj na kategorije",
                        callback_data="category_back",
                    )
                ]
            ]
        ),
    )


# /resetfilters
async def resetfilters(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update):
        await update.message.reply_text("This is a personal bot")
        return

    if len(context.args) != 1:
        await update.message.reply_text("Usage: /resetfilters")
        return

    # get the default filters
    filters = copy.deepcopy(default_filters)

    save_filters(filters)

    await update.message.reply_text(
        "Filters reset to default. Use /settings to view them "
    )


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

    # commands
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("jobs", jobs))
    app.add_handler(CommandHandler("subscribe", subscribe))
    app.add_handler(CommandHandler("unsubscribe", unsubscribe))
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
