"""Check this week's comic and add it to the top of comic/comics.json.

Checks the entry against COMIC_FORMAT.md and checks the SVG is safe to
publish (no scripts, no links or images loaded from elsewhere). Refuses and
writes nothing if anything is wrong.

Usage: python3 _feedbot/add_comic.py ENTRY.json [--dry-run]
"""
import datetime
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
COMICS = ROOT / "comic" / "comics.json"
DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
BANNED_ELEMENTS = {"script", "foreignObject", "iframe", "object", "embed", "image", "a",
                   "animate", "animateMotion", "animateTransform", "set", "audio", "video"}
MAX_SVG_BYTES = 400_000


def plain_text(value, field, errors, required=True, limit=None):
    if value is None or (isinstance(value, str) and not value.strip()):
        if required:
            errors.append(f"{field} is empty")
        return
    if not isinstance(value, str):
        errors.append(f"{field} must be text")
    elif "<" in value or ">" in value:
        errors.append(f"{field} contains HTML")
    elif limit and len(value) > limit:
        errors.append(f"{field} is {len(value)} characters, max {limit}")


def check_svg(path, errors):
    if not path.exists():
        errors.append(f"image file {path.relative_to(ROOT)} does not exist")
        return
    raw = path.read_bytes()
    if len(raw) > MAX_SVG_BYTES:
        errors.append(f"SVG is {len(raw)} bytes, max {MAX_SVG_BYTES}")
    if re.search(rb"<!DOCTYPE|<!ENTITY", raw, re.I):
        errors.append("SVG must not contain a DOCTYPE or ENTITY")
        return
    try:
        root = ET.fromstring(raw)
    except ET.ParseError as e:
        errors.append(f"SVG is not valid XML: {e}")
        return
    if root.tag.split("}")[-1] != "svg":
        errors.append("SVG's root element must be <svg>")
    if not root.get("viewBox"):
        errors.append("SVG needs a viewBox")
    for node in root.iter():
        name = node.tag.split("}")[-1]
        if name in BANNED_ELEMENTS:
            errors.append(f"SVG uses <{name}>, which isn't allowed")
        if name == "style" and node.text and re.search(r"@import|url\((?!\s*['\"]?#)", node.text):
            errors.append("SVG <style> must not import or load anything")
        for attr, value in node.attrib.items():
            attr_name = attr.split("}")[-1].lower()
            if attr_name.startswith("on"):
                errors.append(f"SVG has an event handler ({attr_name}), which isn't allowed")
            if attr_name == "href" and not value.startswith("#"):
                errors.append(f"SVG links to {value!r}; only links within the file (#id) are allowed")
            if "javascript:" in value.lower() or re.search(r"url\((?!\s*['\"]?#)", value):
                errors.append(f"SVG attribute {attr_name} loads something from outside the file")


def check_entry(c, comics, errors):
    plain_text(c.get("model"), "model", errors, limit=80)
    plain_text(c.get("title"), "title", errors, limit=120)
    plain_text(c.get("alt"), "alt", errors, limit=500)
    plain_text(c.get("caption"), "caption", errors, required=False, limit=300)

    posted = c.get("posted") or ""
    if not DATE.match(posted):
        errors.append("posted must be YYYY-MM-DD")
        return
    posted_day = datetime.date.fromisoformat(posted)
    iso = posted_day.isocalendar()
    week = f"{iso[0]}-W{iso[1]:02d}"
    if c.get("week") != week:
        errors.append(f"week must be {week!r} (the ISO week of the posted date)")
    if any(x.get("week") == week for x in comics):
        errors.append(f"there is already a comic for {week}")
    if c.get("image") != f"{week}.svg":
        errors.append(f"image must be {week}.svg")
    else:
        check_svg(ROOT / "comic" / c["image"], errors)

    story = c.get("story") or {}
    if not re.match(r"^https?://", story.get("url") or ""):
        errors.append("story.url must start with http:// or https://")
    elif any((x.get("story") or {}).get("url") == story["url"] for x in comics):
        errors.append("this story already has a comic")
    plain_text(story.get("title"), "story.title", errors, limit=300)
    plain_text(story.get("source"), "story.source", errors, limit=80)
    published = story.get("published") or ""
    if not DATE.match(published):
        errors.append("story.published must be YYYY-MM-DD")
    else:
        age = (posted_day - datetime.date.fromisoformat(published)).days
        if not 0 <= age <= 8:
            errors.append(f"story was published {age} days before posting; it must be from the previous week (0-8 days)")

    notes = c.get("rationale") or {}
    for key in ("why_this_story", "how_the_joke_works", "intended_landing"):
        plain_text(notes.get(key), f"rationale.{key}", errors, limit=600)


def main():
    entry_path = Path(sys.argv[1])
    dry_run = "--dry-run" in sys.argv
    entry = json.loads(entry_path.read_text())
    data = json.loads(COMICS.read_text()) if COMICS.exists() else {"comics": []}

    errors = []
    check_entry(entry, data["comics"], errors)
    if errors:
        print("REFUSED. Nothing was written. Fix these and run again:")
        print("\n".join("  - " + e for e in errors))
        sys.exit(1)

    fields = ["week", "posted", "model", "title", "image", "alt", "caption", "story", "rationale"]
    clean = {k: entry.get(k) for k in fields}
    clean["story"] = {k: entry["story"].get(k) for k in ("title", "url", "source", "published")}
    clean["rationale"] = {k: entry["rationale"][k] for k in ("why_this_story", "how_the_joke_works", "intended_landing")}

    if dry_run:
        print(f"DRY RUN OK: {entry['week']} would be comic #{len(data['comics']) + 1}. Nothing was written.")
        return
    data["comics"] = [clean] + data["comics"]
    COMICS.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    print(f"OK: added {entry['week']} as comic #{len(data['comics'])}.")


if __name__ == "__main__":
    main()
