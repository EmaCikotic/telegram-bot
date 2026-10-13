from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from categories import category_groups
from access import is_owner
from filter_storage import load_filters, save_filters


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
