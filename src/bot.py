import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from scraper import fetch_student_jobs
import asyncio

load_dotenv()

token = os.getenv("TELEGRAM_BOT_TOKEN")


if token:
    print("sucessfully read")
else:
    print("there is no token")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("The bot is working")


async def jobs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Looking for jobs...")
    ads = await asyncio.to_thread(fetch_student_jobs)
    number_of_ads = len(ads)
    await update.message.reply_text(f"Found {number_of_ads} jobs")
    #send all found jobs
    for advert in ads:
        message = (
            f"Title: {advert['title']}\n"
            f"Company: {advert['company']}\n"
            f"Location: {advert['location']}\n"
            f"Pay: {advert['pay']}\n"
            f"Link: {advert['link']}"
        )
        await update.message.reply_text(message)


app = Application.builder().token(token).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("jobs", jobs))

print("Bot is listening send  /start in Telegram.")
app.run_polling()
