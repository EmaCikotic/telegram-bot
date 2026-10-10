import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes


load_dotenv()

token = os.getenv("TELEGRAM_BOT_TOKEN")


if token:
    print("sucessfully read")
else:
    print("there is no token")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("The bot is working")


app = Application.builder().token(token).build()

app.add_handler(CommandHandler("start", start))

print("Bot is listening send  /start in Telegram.")
app.run_polling()
