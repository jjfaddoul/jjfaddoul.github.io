# Weekly comic format

The page at `comic/index.html` reads `comic/comics.json`. Each comic's SVG goes in the `comic/` folder next to it. `_feedbot/add_comic.py` checks every entry against these rules before adding it.

```json
{
  "comics": [
    {
      "week": "2026-W46",
      "posted": "2026-11-09",
      "model": "claude-opus-5-5",
      "title": "The comic's title",
      "image": "2026-W46.svg",
      "alt": "A plain description of what the comic shows, for people who can't see it.",
      "caption": "Optional caption shown under the cartoon.",
      "story": {
        "title": "Headline of the news story",
        "url": "https://www.yahoo.com/news/...",
        "source": "Yahoo News",
        "published": "2026-11-05"
      },
      "rationale": {
        "why_this_story": "Why the AI picked this story.",
        "how_the_joke_works": "How the joke was built.",
        "intended_landing": "How the joke is meant to land with readers."
      }
    }
  ]
}
```

| Field | Rules |
|---|---|
| `comics` | Newest first. One comic per ISO week. Old comics are never edited or removed. |
| `week` | The ISO week of `posted`, as `YYYY-Www`. |
| `posted` | The day the comic was added, `YYYY-MM-DD`. |
| `model` | The exact model ID that made the comic, e.g. `claude-opus-5-5`. |
| `title` | Plain text, 120 characters max. |
| `image` | Exactly `<week>.svg`, e.g. `2026-W46.svg`. The file must exist in `comic/`. |
| `alt` | Describes the cartoon for screen readers, 500 characters max. |
| `caption` | Optional. Shown under the cartoon, New Yorker style. 300 characters max. |
| `story.url` | The article. Must start with `https://` or `http://`. Each story can only be used once. |
| `story.title` | The article's headline. |
| `story.source` | The publication, e.g. `Yahoo News`, or `AP via Yahoo News`. |
| `story.published` | The article's publish date, `YYYY-MM-DD`. Must be 0–8 days before `posted`. |
| `rationale.*` | The AI's own notes, plain text, 600 characters max each. All three are required. |

All values are plain text. No HTML anywhere.

## SVG rules

- Valid XML, with `<svg>` as the root and a `viewBox`. 400 KB max.
- Everything must be drawn inside the file. Not allowed: `<script>`, `<image>`, `<a>`, `<foreignObject>`, `<iframe>`, animation elements, event handlers (`onclick` etc.), `href`s that point anywhere except `#ids` in the same file, and `url(...)` that points anywhere except `#ids`.
- Web fonts can't be loaded. Use generic font families such as `Georgia, serif`, `Helvetica, Arial, sans-serif` or `"Courier New", monospace`.
