from database import get_database
import os
from filter_storage import load_database_filters

database = get_database()

owner_user_id = os.getenv("OWNER_USER_ID")

if not owner_user_id:
    raise SystemExit("No user id in .env")

owner_user_id = int(owner_user_id)

filters = load_database_filters(owner_user_id)

print(filters)
result = database.table("bot_users").select("telegram_user_id").limit(1).execute()

#print("Database connection successful.")
#print("Rows returned:", len(result.data))
