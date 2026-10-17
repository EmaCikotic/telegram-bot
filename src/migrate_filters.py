import os

from database import get_database
from filter_storage import load_filters

database = get_database()

owner_user_id = os.getenv("OWNER_USER_ID")

if not owner_user_id:
    raise SystemExit("Missing owner user id in .env")

owner_user_id = int(owner_user_id)

filters = load_filters()


row = {
    "telegram_user_id": owner_user_id,
    "categories": filters["categories"],
    "regions": filters["regions"],
    "min_pay": filters["min_pay"],
    "max_pay": filters["max_pay"],
}


database.table("user_filters").insert(row).execute()
print("Filters copied to Supabase.")


