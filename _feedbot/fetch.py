"""Fetch today's candidate items for the feed.

Builds a pool of recent items from every source, skips anything already in
feed/items.json, and writes the pool to a JSON file. The daily task picks
which items to publish and writes their descriptions. Standard library only.

Usage: python3 _feedbot/fetch.py OUT.json
"""
import datetime
import email.utils
import gzip
import html
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ITEMS = ROOT / "feed" / "items.json"
UA = "jjfaddoul-feed-bot/1.0 (+https://jjfaddoul.github.io/feed/)"
NOW = datetime.datetime.now(datetime.timezone.utc)
TODAY = datetime.date.today()

# name, category, url, how many newest items go in the pool, max age in hours
RSS_SOURCES = [
    ("TechCrunch", "tech", "https://techcrunch.com/feed/", 6, 24),
    ("Ars Technica", "tech", "https://feeds.arstechnica.com/arstechnica/index", 6, 24),
    ("Hackaday", "tech", "https://hackaday.com/blog/feed/", 3, 24),
    ("SMBC", "comics", "https://www.smbc-comics.com/comic/rss", 1, 168),
    ("Poorly Drawn Lines", "comics", "https://poorlydrawnlines.com/feed/", 1, 168),
    ("Existential Comics", "comics", "https://existentialcomics.com/rss.xml", 1, 168),
    ("The Oatmeal", "comics", "https://theoatmeal.com/feed/rss", 1, 168),
    ("Dinosaur Comics", "comics", "https://www.qwantz.com/rssfeed.php", 1, 168),
    ("War and Peas", "comics", "https://warandpeas.com/feed/", 1, 168),
    ("Colossal", "art", "https://www.thisiscolossal.com/feed/", 3, 48),
    ("Public Domain Review", "art", "https://publicdomainreview.org/rss.xml", 2, 168),
    ("Louder", "music", "https://www.loudersound.com/feeds/all", 4, 24),
    ("Stereogum", "music", "https://stereogum.com/feed", 4, 24),
    ("1000-Word Philosophy", "philosophy", "https://1000wordphilosophy.com/feed/", 1, 168),
    ("Daily Nous", "philosophy", "https://dailynous.com/feed/", 2, 48),
    ("UN News", "humanitarian", "https://news.un.org/feed/subscribe/en/news/all/rss.xml", 3, 24),
    ("Positive News", "humanitarian", "https://www.positive.news/feed/", 3, 48),
    ("FlowingData", "visual", "https://flowingdata.com/feed/", 2, 48),
    ("Quanta Magazine", "nerdy", "https://www.quantamagazine.org/feed/", 2, 48),
]

# Titles to skip, per source.
SKIP_TITLES = {"UN News": re.compile(r"news in brief", re.I)}

# Strip these prefixes from titles.
TITLE_PREFIXES = {"SMBC": "Saturday Morning Breakfast Cereal - "}


def get(url, timeout=20):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Encoding": "gzip"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        body = r.read()
        if r.headers.get("Content-Encoding") == "gzip" or body[:2] == b"\x1f\x8b":
            body = gzip.decompress(body)
        return body


def get_json(url):
    return json.loads(get(url))


def clean_url(url):
    """Drop tracking parameters so the same page always has the same URL."""
    parts = urllib.parse.urlsplit(url.strip())
    query = [(k, v) for k, v in urllib.parse.parse_qsl(parts.query) if not k.startswith("utm_")]
    return urllib.parse.urlunsplit(parts._replace(query=urllib.parse.urlencode(query)))


def plain(text, limit=600):
    text = re.sub(r"<[^>]+>", " ", text or "")
    text = re.sub(r"\s+", " ", html.unescape(text)).strip()
    text = re.sub(r"\s*The (post|article) .* appeared first on .*$", "", text)  # WordPress footer
    return text[:limit]


def parse_date(text):
    if not text:
        return None
    text = text.strip()
    try:
        d = email.utils.parsedate_to_datetime(text)
    except (TypeError, ValueError):
        try:
            d = datetime.datetime.fromisoformat(text.replace("Z", "+00:00"))
        except ValueError:
            return None
    if d.tzinfo is None:
        d = d.replace(tzinfo=datetime.timezone.utc)
    return d


def og_image(url):
    try:
        body = get(url, timeout=15)[:300000].decode("utf-8", "ignore")
    except Exception:
        return None
    for pattern in (r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)',
                    r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:image["\']'):
        m = re.search(pattern, body)
        if m:
            return html.unescape(m.group(1))
    return None


def tag(e):
    return e.tag.split("}")[-1]


def rss_entries(body):
    root = ET.fromstring(body)
    for it in root.iter():
        if tag(it) not in ("item", "entry"):
            continue
        d = {"title": "", "link": "", "date": None, "image": None, "summary": ""}
        for c in it:
            t = tag(c)
            if t == "title":
                d["title"] = plain(c.text, 300)
            elif t == "link" and not d["link"]:
                d["link"] = (c.get("href") or c.text or "").strip()
            elif t in ("pubDate", "published", "date") or (t == "updated" and not d["date"]):
                d["date"] = parse_date(c.text) or d["date"]
            elif t in ("content", "thumbnail") and c.get("url") and not d["image"]:
                if t == "thumbnail" or "image" in (c.get("medium", "") + c.get("type", "image")):
                    d["image"] = c.get("url")
            elif t == "enclosure" and "image" in (c.get("type") or "") and not d["image"]:
                d["image"] = c.get("url")
            elif t in ("description", "encoded", "summary") and c.text:
                if not d["image"]:
                    m = re.search(r'<img[^>]+src=["\']([^"\']+)', c.text)
                    if m:
                        d["image"] = html.unescape(m.group(1))
                if t != "encoded" or not d["summary"]:
                    d["summary"] = plain(c.text)
        yield d


def item(source, category, url, title, image, published, summary, **extra):
    d = {
        "url": clean_url(url),
        "title": title,
        "description": "",
        "image": image,
        "source": source,
        "category": category,
        "published": published,
        "added": TODAY.isoformat(),
        "summary": summary,
    }
    d.update(extra)
    return d


def fetch_rss(name, category, url, count, max_age, seen):
    entries = [e for e in rss_entries(get(url))
               if e["link"] and e["title"] and e["date"]
               and NOW - e["date"] <= datetime.timedelta(hours=max_age)
               and not (name in SKIP_TITLES and SKIP_TITLES[name].search(e["title"]))]
    entries.sort(key=lambda e: e["date"], reverse=True)

    # Only the newest `count` entries are eligible. If they're already in the
    # feed, add nothing rather than reaching back for older ones.
    out = []
    for e in entries[:count]:
        link = clean_url(e["link"])
        if link in seen:
            continue
        title = e["title"]
        prefix = TITLE_PREFIXES.get(name)
        if prefix and title.startswith(prefix):
            title = title[len(prefix):]
        image = e["image"] or og_image(link)
        out.append(item(name, category, link, title, image, e["date"].date().isoformat(), e["summary"]))
    return out


def fetch_hacker_news(seen):
    # The front page's top 15 stories. Ones already in the feed are skipped,
    # not replaced by stories further down.
    stories = []
    for story_id in get_json("https://hacker-news.firebaseio.com/v0/topstories.json")[:25]:
        if len(stories) >= 15:
            break
        s = get_json(f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json") or {}
        if s.get("type") == "story" and s.get("title"):
            stories.append(s)

    out = []
    for s in stories:
        link = clean_url(s.get("url") or f"https://news.ycombinator.com/item?id={s['id']}")
        if link in seen:
            continue
        published = datetime.datetime.fromtimestamp(s["time"], datetime.timezone.utc).date().isoformat()
        summary = plain(s.get("text")) or f"{s.get('score', 0)} points on Hacker News."
        image = og_image(link) if s.get("url") else None
        out.append(item("Hacker News", "tech", link, s["title"], image, published, summary))
    return out


def fetch_xkcd(seen):
    c = get_json("https://xkcd.com/info.0.json")
    link = f"https://xkcd.com/{c['num']}/"
    published = datetime.date(int(c["year"]), int(c["month"]), int(c["day"]))
    if link in seen or TODAY - published > datetime.timedelta(days=7):
        return []
    return [item("XKCD", "comics", link, c["safe_title"], c["img"], published.isoformat(), c.get("alt", ""))]


def fetch_met(seen):
    base = "https://collectionapi.metmuseum.org/public/collection/v1.1/search?q=*&isHighlight=true&hasImages=true"
    total = get_json(base + "&limit=1")["total"]
    offset = (TODAY.toordinal() * 7) % max(total - 30, 1)
    options = []
    for object_id in get_json(f"{base}&offset={offset}&limit=30")["objectIDs"]:
        if len(options) >= 3:
            break
        o = get_json(f"https://collectionapi.metmuseum.org/public/collection/v1/objects/{object_id}")
        time.sleep(0.2)
        if not o.get("isPublicDomain") or not o.get("primaryImageSmall") or not o.get("objectURL"):
            continue
        if clean_url(o["objectURL"]) in seen:
            continue
        artist = o.get("artistDisplayName") or o.get("culture") or "Unknown artist"
        summary = "; ".join(x for x in (artist, o.get("objectDate"), o.get("medium"), o.get("department")) if x)
        options.append(item("The Met", "art", o["objectURL"], f"{o['title']} — {artist}", o["primaryImageSmall"],
                            TODAY.isoformat(), summary, choose_one=True))
    return options


def fetch_wikimedia_potd(seen):
    d = get_json(f"https://en.wikipedia.org/api/rest_v1/feed/featured/{TODAY:%Y/%m/%d}")
    img = d.get("image") or {}
    if not img.get("file_page") or clean_url(img["file_page"]) in seen:
        return []
    summary = plain((img.get("description") or {}).get("text"))
    return [item("Wikimedia Picture of the Day", "visual", img["file_page"], img.get("title", ""),
                 (img.get("thumbnail") or {}).get("source"), TODAY.isoformat(), summary, write_title=True)]


def fetch_on_this_day(seen):
    d = get_json(f"https://en.wikipedia.org/api/rest_v1/feed/onthisday/selected/{TODAY:%m/%d}")
    options = []
    for event in d.get("selected", []):
        for page in event.get("pages", []):
            link = ((page.get("content_urls") or {}).get("desktop") or {}).get("page")
            image = (page.get("thumbnail") or {}).get("source")
            if link and image and clean_url(link) not in seen:
                options.append(item("Wikipedia On this day", "nerdy", link, f"On this day in {event['year']}",
                                    image, TODAY.isoformat(), plain(event.get("text")), choose_one=True))
                break
    return options[:8]


def main():
    out_path = Path(sys.argv[1])
    existing = json.loads(ITEMS.read_text()) if ITEMS.exists() else {"items": []}
    seen = {clean_url(i["url"]) for i in existing.get("items", [])}
    # Daily picks get one item per day, even if the task runs twice.
    picked_today = {i["source"] for i in existing.get("items", []) if i.get("added") == TODAY.isoformat()}
    daily_picks = {"The Met", "Wikimedia Picture of the Day", "Wikipedia On this day"}

    jobs = [("Hacker News", lambda: fetch_hacker_news(seen)), ("XKCD", lambda: fetch_xkcd(seen))]
    jobs += [(s[0], (lambda s=s: fetch_rss(*s, seen))) for s in RSS_SOURCES]
    jobs += [("The Met", lambda: fetch_met(seen)),
             ("Wikimedia Picture of the Day", lambda: fetch_wikimedia_potd(seen)),
             ("Wikipedia On this day", lambda: fetch_on_this_day(seen))]

    candidates, report = [], []
    for name, job in jobs:
        if name in daily_picks and name in picked_today:
            report.append(f"{name}: 0 new (already picked today)")
            continue
        try:
            found = job()
        except Exception as e:
            report.append(f"ERROR {name}: {e.__class__.__name__}: {e}")
            continue
        for c in found:
            seen.add(c["url"])
        candidates += found
        report.append(f"{name}: {len(found)} new")

    day = {"date": TODAY.isoformat(), "model": "", "note": "", "candidates": candidates}
    out_path.write_text(json.dumps(day, indent=2, ensure_ascii=False))
    # An untouched copy, so merge.py can check the task didn't change or invent items.
    out_path.with_suffix(".orig.json").write_text(json.dumps(day, indent=2, ensure_ascii=False))
    print("\n".join(report))
    print(f"TOTAL: {len(candidates)} candidates written to {out_path}")


if __name__ == "__main__":
    main()
