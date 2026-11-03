"""Check this week's joke, publish it to joke.txt and log it in _feedbot/jokes.json.

Refuses and writes nothing if the joke isn't plain text of a sensible size,
repeats an earlier joke, or this week already has one.

Usage: python3 _feedbot/set_joke.py ENTRY.json [--dry-run]
ENTRY.json: {"joke": "...", "model": "claude-..."}
"""
import datetime
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
JOKE = ROOT / "joke.txt"
LOG = ROOT / "_feedbot" / "jokes.json"
MAX_CHARS = 280
MAX_LINES = 4


def normalise(text):
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


def main():
    entry = json.loads(Path(sys.argv[1]).read_text())
    dry_run = "--dry-run" in sys.argv
    log = json.loads(LOG.read_text()) if LOG.exists() else {"jokes": []}

    today = datetime.date.today()
    iso = today.isocalendar()
    week = f"{iso[0]}-W{iso[1]:02d}"

    joke = (entry.get("joke") or "").strip()
    model = (entry.get("model") or "").strip()
    errors = []
    if not joke:
        errors.append("joke is empty")
    if "<" in joke or ">" in joke:
        errors.append("joke contains < or >; it must be plain text")
    if len(joke) > MAX_CHARS:
        errors.append(f"joke is {len(joke)} characters, max {MAX_CHARS}")
    if len(joke.splitlines()) > MAX_LINES:
        errors.append(f"joke is {len(joke.splitlines())} lines, max {MAX_LINES}")
    if not model or "<" in model or len(model) > 80:
        errors.append("model must be the model ID, as plain text")
    if any(j["week"] == week for j in log["jokes"]):
        errors.append(f"there is already a joke for {week}")
    if any(normalise(j["joke"]) == normalise(joke) for j in log["jokes"]):
        errors.append("this joke has already been used")

    if errors:
        print("REFUSED. Nothing was written. Fix these and run again:")
        print("\n".join("  - " + e for e in errors))
        sys.exit(1)

    if dry_run:
        print(f"DRY RUN OK: {week}'s joke would be published. Nothing was written.")
        return
    log["jokes"] = [{"week": week, "posted": today.isoformat(), "model": model, "joke": joke}] + log["jokes"]
    LOG.write_text(json.dumps(log, indent=2, ensure_ascii=False) + "\n")
    JOKE.write_text(joke + "\n")
    print(f"OK: published {week}'s joke to joke.txt and logged it.")


if __name__ == "__main__":
    main()
