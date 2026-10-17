import copy
import json
from pathlib import Path
from scraper import default_filters
from database import get_database

PROJECT_ROOT = Path(__file__).resolve().parent.parent  # finds the folder
FILTERS_FILE = PROJECT_ROOT / "data" / "filters.json"
FILTERS_FILE.parent.mkdir(parents=True, exist_ok=True)


def load_database_filters(user_id):
    database = get_database()

    result = (
        database.table("user_filters")
        .select("categories, regions, min_pay, max_pay")
        .eq("telegram_user_id", user_id)
        .execute()
    )

    if not result.data:
        return copy.deepcopy(default_filters)

    else:
        return result.data[0]


def load_filters():
    if not FILTERS_FILE.exists():
        return copy.deepcopy(default_filters)
    else:
        filters_text = FILTERS_FILE.read_text(encoding="utf-8")

        try:
            filters = json.loads(filters_text)  # turn into dictionary
        except json.JSONDecodeError:
            raise RuntimeError(
                "Filters file contains invalid JSON. Fix it before continuing"
            )

    return filters


def save_filters(filters):
    filter_json = json.dumps(filters, indent=2)

    FILTERS_FILE.write_text(filter_json, encoding="utf-8")
