from pathlib import Path
from pprint import pformat
import requests
from bs4 import BeautifulSoup


def extract_category_groups():
    response = requests.get(
        "https://www.studentski-servis.com/studenti/prosta-dela", timeout=30
    )
    response.raise_for_status()
    soup = BeautifulSoup(response.content, "html.parser")
    groups = {}

    def label_for(checkbox):
        label = soup.find("label", attrs={"for": checkbox["id"]})
        if label is None:
            raise ValueError(f"Missing label for category {checkbox['value']}")
        return label.get_text(" ", strip=True)

    checkboxes = soup.select('input[name="skD[]"]')
    for checkbox in checkboxes:
        code = checkbox["value"]
        if not code.isdigit():
            continue
        container = checkbox.find_parent(
            "div", attrs={"data-ess-component": "componentMultiCheckbox"}
        )
        if container is None:
            raise ValueError(f"Missing group container for {code}")
        children = {}
        for child in container.select('input[name="skD[]"]'):
            if child["value"] != code:
                children[child["value"]] = label_for(child)
        groups[code] = {"name": label_for(checkbox), "children": children}

    mapped = list(groups) + [code for g in groups.values() for code in g["children"]]
    expected = {checkbox["value"] for checkbox in checkboxes}
    if not groups or len(mapped) != len(set(mapped)) or set(mapped) != expected:
        raise ValueError("Category extraction is incomplete or contains duplicates.")
    return groups


if __name__ == "__main__":
    category_groups = extract_category_groups()
    destination = Path(__file__).with_name("categories.py")
    source = (
        "# Category codes and original Slovenian labels from e-Študentski Servis.\n\n"
        "category_groups = "
        + pformat(category_groups, width=100, sort_dicts=False)
        + "\n"
    )
    destination.write_text(source, encoding="utf-8")
    print(f"Saved {len(category_groups)} category groups to {destination.name}.")
