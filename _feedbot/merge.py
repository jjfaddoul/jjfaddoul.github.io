"""Check today's finished candidates and add them to the top of feed/items.json.

Every candidate must have a description written. Refuses the whole batch if
anything breaks the rules in FORMAT.md, so a bad run never reaches the site.

Usage: python3 _feedbot/merge.py CANDIDATES.json [--dry-run]
"""
import datetime
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ITEMS = ROOT / "feed" / "items.json"
CATEGORIES = {"tech", "comics", "art", "music", "philosophy", "humanitarian", "visual", "nerdy"}
FIELDS = ["url", "title", "description", "image", "source", "category", "published", "added"]
DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def problems(c, seen):
    p = []
    if not re.match(r"^https?://", c.get("url") or ""):
        p.append("url must start with http:// or https://")
    elif c["url"] in seen:
        p.append("url is already in the feed")
    for field in ("title", "description", "source"):
        value = c.get(field)
        if not isinstance(value, str) or not value.strip():
            p.append(f"{field} is empty")
        elif "<" in value or ">" in value:
            p.append(f"{field} contains HTML")
    if len(c.get("description") or "") > 200:
        p.append(f"description is {len(c['description'])} characters, max 200")
    if c.get("image") is not None and not re.match(r"^https?://", c["image"]):
        p.append("image must be null or start with http:// or https://")
    if c.get("category") not in CATEGORIES:
        p.append(f"category {c.get('category')!r} is not allowed")
    for field in ("published", "added"):
        if not DATE.match(c.get(field) or ""):
            p.append(f"{field} must be YYYY-MM-DD")
    return p


def main():
    path = Path(sys.argv[1])
    dry_run = "--dry-run" in sys.argv
    candidates = json.loads(path.read_text())["candidates"]
    feed = json.loads(ITEMS.read_text()) if ITEMS.exists() else {"updated": None, "items": []}
    seen = {i["url"] for i in feed["items"]}

    errors = []
    choose_one = [c for c in candidates if c.get("choose_one")]
    if len(choose_one) > 1:
        errors.append(f"{len(choose_one)} 'Wikipedia On this day' items left; keep exactly one")

    new = []
    for n, c in enumerate(candidates):
        for problem in problems(c, seen):
            errors.append(f"candidate {n} ({c.get('source')}: {c.get('title')!r}): {problem}")
        seen.add(c.get("url"))
        new.append({field: c.get(field) for field in FIELDS})

    if errors:
        print("REFUSED. Nothing was written. Fix these and run merge again:")
        print("\n".join("  - " + e for e in errors))
        sys.exit(1)

    if not new:
        print("Nothing new today. feed/items.json was not changed.")
        return

    feed["items"] = new + feed["items"]
    feed["updated"] = datetime.datetime.now().astimezone().isoformat(timespec="seconds")
    if dry_run:
        print(f"DRY RUN OK: would add {len(new)} items ({len(feed['items'])} total). Nothing was written.")
        return
    ITEMS.write_text(json.dumps(feed, indent=2, ensure_ascii=False) + "\n")
    print(f"OK: added {len(new)} items. The feed now has {len(feed['items'])} items.")


if __name__ == "__main__":
    main()
