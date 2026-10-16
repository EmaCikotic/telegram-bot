import os
from pathlib import Path

from dotenv import load_dotenv
from supabase import create_client


def get_database():
    
    project_root = Path(__file__).resolve().parent.parent
    load_dotenv(project_root / ".env")

    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SECRET_KEY")

    if not url or not key:
        raise SystemExit("Missing Supabase settings in .env.")

    return create_client(url, key)

   

