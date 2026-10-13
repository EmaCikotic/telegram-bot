import copy
import math

from telegram import Update
from telegram.ext import ContextTypes

from access import is_owner
from filter_storage import load_filters, save_filters
from locations import location_options
from scraper import default_filters


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


# /resetfilters
async def resetfilters(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update):
        await update.message.reply_text("This is a personal bot")
        return

    if len(context.args) != 0:
        await update.message.reply_text("Usage: /resetfilters")
        return

    # get the default filters
    filters = copy.deepcopy(default_filters)

    save_filters(filters)

    await update.message.reply_text(
        "Filters reset to default. Use /settings to view them "
    )
