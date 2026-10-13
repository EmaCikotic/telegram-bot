import copy
import json
from pathlib import Path
from scraper import default_filters

PROJECT_ROOT = Path(__file__).resolve().parent.parent  # finds the folder
FILTERS_FILE = PROJECT_ROOT / "data" / "filters.json"
FILTERS_FILE.parent.mkdir(parents=True, exist_ok=True)


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
