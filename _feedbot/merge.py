"""Check today's picks and add them to the top of feed/items.json.

The daily task marks the candidates it wants with "pick": true, writes their
descriptions, and writes a note about the day's picks. This refuses the whole
batch if anything breaks the rules in FORMAT.md, so a bad run never reaches
the site.

Usage: python3 _feedbot/merge.py TODAY.json [--dry-run]
(fetch.py also wrote TODAY.orig.json next to it; this checks against it.)
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
LOCKED = ["image", "source", "category", "published", "added"]  # never changed by the task
DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
MIN_PICKS, MAX_PICKS = 10, 25


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
    day = json.loads(path.read_text())
    original = {c["url"]: c for c in json.loads(path.with_suffix(".orig.json").read_text())["candidates"]}
    feed = json.loads(ITEMS.read_text()) if ITEMS.exists() else {"updated": None, "items": []}
    feed.setdefault("notes", {})
    seen = {i["url"] for i in feed["items"]}

    errors = []
    picks = [c for c in day["candidates"] if c.get("pick") is True]
    need = min(MIN_PICKS, len(original))
    if not need <= len(picks) <= MAX_PICKS:
        errors.append(f"{len(picks)} items picked; pick between {need} and {MAX_PICKS}")

    for source in {c["source"] for c in picks if original.get(c.get("url"), {}).get("choose_one")}:
        n = sum(1 for c in picks if c["source"] == source)
        if n > 1:
            errors.append(f"{n} '{source}' items picked; pick at most one")

    for n, c in enumerate(picks):
        label = f"pick {n} ({c.get('source')}: {c.get('title')!r})"
        o = original.get(c.get("url"))
        if not o:
            errors.append(f"{label}: url isn't in today's pool; never change urls or add items")
            continue
        for field in LOCKED:
            if c.get(field) != o.get(field):
                errors.append(f"{label}: {field} was changed; it must stay as fetched")
        if c.get("title") != o["title"] and not o.get("write_title"):
            errors.append(f"{label}: title was changed; only write_title items may change it")
        for problem in problems(c, seen):
            errors.append(f"{label}: {problem}")
        seen.add(c.get("url"))

    note, model = (day.get("note") or "").strip(), (day.get("model") or "").strip()
    if picks:
        if not note:
            errors.append("note is empty; write a note about today's picks")
        elif "<" in note or ">" in note or len(note) > 400:
            errors.append("note must be plain text, 400 characters max")
        if not model or "<" in model or len(model) > 80:
            errors.append("model must be the model ID, as plain text")

    if errors:
        print("REFUSED. Nothing was written. Fix these and run merge again:")
        print("\n".join("  - " + e for e in errors))
        sys.exit(1)

    if not picks:
        print("Nothing new today. feed/items.json was not changed.")
        return

    feed["items"] = [{f: c.get(f) for f in FIELDS} for c in picks] + feed["items"]
    feed["notes"].setdefault(day["date"], {"model": model, "note": note})  # keep the first note if run twice
    feed["updated"] = datetime.datetime.now().astimezone().isoformat(timespec="seconds")
    if dry_run:
        print(f"DRY RUN OK: would add {len(picks)} of {len(original)} items ({len(feed['items'])} total). Nothing was written.")
        return
    ITEMS.write_text(json.dumps(feed, indent=2, ensure_ascii=False) + "\n")
    print(f"OK: added {len(picks)} of {len(original)} items. The feed now has {len(feed['items'])} items.")


if __name__ == "__main__":
    main()
