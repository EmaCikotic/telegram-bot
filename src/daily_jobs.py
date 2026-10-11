import asyncio
from telegram import Bot
from bot import token, send_new_jobs


async def main():
    async with Bot(token=token) as bot:
        await send_new_jobs(bot)


if __name__ == "__main__":
    asyncio.run(main())
