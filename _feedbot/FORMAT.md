# Feed item format

The feed page reads `feed/items.json`. The daily task adds new items to it.

```json
{
  "updated": "2026-11-03T07:00:00+08:00",
  "items": [
    {
      "url": "https://xkcd.com/3319/",
      "title": "Elevators",
      "description": "One or two sentences written for this feed. Under 200 characters.",
      "image": "https://imgs.xkcd.com/comics/elevators.png",
      "source": "XKCD",
      "category": "comics",
      "published": "2026-11-02",
      "added": "2026-11-03"
    }
  ],
  "notes": {
    "2026-11-04": {
      "model": "claude-sonnet-5-5",
      "note": "The AI's note about the day's picks, shown above that day's cards."
    }
  }
}
```

| Field | Rules |
|---|---|
| `updated` | When the file was last written, ISO 8601 with timezone. |
| `items` | Newest first. New items go at the top. Old items are never edited or removed. |
| `url` | The original page. Must start with `https://` or `http://`. This is also the item's identity: never add an item whose `url` is already in the file. |
| `title` | The original title, as plain text. Strip site prefixes like "Saturday Morning Breakfast Cereal - ". |
| `description` | Written fresh, never copied. 1–2 sentences, under 200 characters, plain text. Don't spoil a comic's punchline. |
| `image` | A direct image URL, or `null` if there isn't one. The page shows a placeholder for `null` or for images that fail to load. |
| `source` | The source's display name, exactly as listed in the task. |
| `category` | One of: `tech`, `comics`, `art`, `music`, `philosophy`, `humanitarian`, `visual`, `nerdy`. |
| `published` | The original publish date, `YYYY-MM-DD`. |
| `added` | The date the task added it, `YYYY-MM-DD`. The page groups cards by this date. |
| `notes` | One entry per day, keyed by date: the model that picked that day's items, and its note (plain text, 400 characters max). Days before the AI picked items have no note. |

All values are plain text. No HTML anywhere.
