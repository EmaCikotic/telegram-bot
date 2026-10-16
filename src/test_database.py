import os
from pathlib import Path

from dotenv import load_dotenv
from supabase import create_client

project_root = Path(__file__).resolve().parent.parent
load_dotenv(project_root / ".env")

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_SECRET_KEY")

if not url or not key:
    raise SystemExit("Missing Supabase settings in .env.")

database = create_client(url, key)

result = (
    database.table("bot_users")
    .select("telegram_user_id")
    .limit(1)
    .execute()
)

print("Database connection successful.")
print("Rows returned:", len(result.data))