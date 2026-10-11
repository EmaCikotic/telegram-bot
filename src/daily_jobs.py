import asyncio
from telegram import Bot
from bot import token, send_new_jobs, load_state, save_state
from scraper import fetch_student_jobs
import os
from bot import PROJECT_ROOT
import json

chat_id = os.getenv("TELEGRAM_CHAT_ID")

if not chat_id:
    raise SystemExit(
        "TELEGRAM_CHAT_ID is missing, make sure you add it to you env file"
    )

chat_id = int(chat_id)

HISTORY_FILE = (
    PROJECT_ROOT / "data" / "job-history.json"
)  # points to the json file inside data


HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)


async def main():
    first_run = not HISTORY_FILE.exists()

    if first_run:
        ads = await asyncio.to_thread(fetch_student_jobs)
        seen_links = []

        for advert in ads:
            seen_links.append(advert["link"])
    else:
        history_text = HISTORY_FILE.read_text(encoding="utf-8")
        seen_links = json.loads(history_text)

    state = {
        "chat_id": chat_id,
        "seen_links": seen_links,
        "enabled": True,
    }
    save_state(state)

    try:
        if first_run:
            print("Initial job history saved. No messages sent.")
            return

        async with Bot(token=token) as bot:
            await send_new_jobs(bot)
    finally:
        updated_state = load_state()
        history_text = json.dumps(updated_state["seen_links"], indent=2)
        HISTORY_FILE.write_text(history_text, encoding="utf-8")


if __name__ == "__main__":
    asyncio.run(main())
