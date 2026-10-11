import asyncio
from telegram import Bot
from bot import token, send_new_jobs, load_state, save_state
from scraper import fetch_student_jobs
import os


chat_id = os.getenv("TELEGRAM_CHAT_ID")

if not chat_id:
    raise SystemExit(
        "TELEGRAM_CHAT_ID is missing, make sure you add it to you env file"
    )

chat_id = int(chat_id)


async def main():
    state = load_state()

    if not state:
        ads = await asyncio.to_thread(fetch_student_jobs)

        seen_links = []
        for advert in ads:
            seen_links.append(advert["link"])

        state = {
            "chat_id": chat_id,
            "seen_links": seen_links,
            "enabled": True,
        }
        save_state(state)
        print("Initial job history saved. No messages sent.")
        return

    async with Bot(token=token) as bot:
        await send_new_jobs(bot)


if __name__ == "__main__":
    asyncio.run(main())
