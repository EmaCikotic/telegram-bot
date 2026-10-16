import os

from database import get_database

database = get_database()

user_id = os.getenv("OWNER_USER_ID")
chat_id = os.getenv("TELEGRAM_CHAT_ID")


if not user_id or not chat_id:
    raise SystemExit("Missing ids in .env.")

user_id = int(user_id)
chat_id = int(chat_id)


user = {"telegram_user_id": user_id, "chat_id": chat_id, "alerts_enabled": False}

database.table("bot_users").insert(user).execute()

print("User saved succesfully")
