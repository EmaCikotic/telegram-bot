import os
from dotenv import load_dotenv


load_dotenv()
owner_user_id = os.getenv("OWNER_USER_ID")

if owner_user_id:
    print("Owner ID successfully read")
else:
    raise SystemExit("Missing OWNER_USER_ID. Add it to your .env file.")

owner_user_id = int(owner_user_id)


def is_owner(update):
    return update.effective_user.id == owner_user_id
