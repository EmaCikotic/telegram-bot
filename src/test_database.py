from database import get_database


database = get_database()

result = database.table("bot_users").select("telegram_user_id").limit(1).execute()

print("Database connection successful.")
print("Rows returned:", len(result.data))
