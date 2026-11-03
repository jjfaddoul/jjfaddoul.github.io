# Daily feed update

You are updating the news feed on https://jjfaddoul.github.io/feed/. Follow these steps in order. Do not skip steps, and do not do anything that isn't listed here.

Work in the repository at `/Users/josephjames/Developer/websites/jjfaddoul.github.io`. Run every command from that folder.

## 1. Sync with GitHub

```bash
git checkout main
git pull --rebase origin main
```

If the pull fails, stop and report the error. Do not try to fix it.

## 2. Fetch today's candidates

```bash
python3 _feedbot/fetch.py _feedbot/today.json
```

This prints one line per source and a total. Some sources having `0 new` is normal. An `ERROR` line means that source failed today: note it for your report and carry on.

If the total is 0, skip to step 6 and report that there was nothing new.

## 3. Write a description for every candidate

Open `_feedbot/today.json`. Each item in `candidates` has an empty `"description"`. Fill in every one.

Rules for descriptions:
- 1–2 sentences, **200 characters or fewer**, plain text. No HTML, no `<` or `>`, no emoji, no hashtags.
- Base it only on the item's `title` and `summary`. Don't add facts that aren't there. If the summary is empty, write from the title alone and keep it short.
- Say what the item is about in plain words. Don't copy sentences from the summary.
- For comics (`"category": "comics"`), say what the comic is about without giving away the joke.
- Neutral and friendly. No clickbait, no "you won't believe".

Some items need extra work:
- **`"write_title": true`** (Wikimedia Picture of the Day): replace `title` with a short, readable title of 80 characters or fewer that says what the picture shows, based on its `summary`. For example, "Orange-lined triggerfish in the Red Sea" instead of "File:Pez ballesta ondulado (...).jpg".
- **`"choose_one": true`** (Wikipedia On this day): there are several options. Keep **exactly one**, preferring an event about science, technology, exploration or culture over war or disaster. Delete the other options from `candidates` entirely.

You may also delete a candidate if it is an advert, a sponsored post, a shopping deal, or a job listing.

Never change `url`, `image`, `source`, `category`, `published` or `added`. Never add new candidates.

Save the file as valid JSON.

## 4. Check and merge

```bash
python3 _feedbot/merge.py _feedbot/today.json
```

- If it prints `OK`, continue.
- If it prints `REFUSED`, it lists exactly what is wrong. Fix those things in `_feedbot/today.json` and run the same command again. Repeat until it prints `OK`. If it still refuses after 3 attempts, stop and report the errors. Do not edit `feed/items.json` by hand.

## 5. Publish

Only `feed/items.json` gets committed. Never commit anything else.

```bash
git add feed/items.json
git commit -m "Feed update YYYY-MM-DD"
git push origin main
```

Replace `YYYY-MM-DD` with today's date. If the push fails, stop and report the error. Never use `--force`.

## 6. Report

Finish with a short report:
- How many items were added, per source.
- Any sources that printed `ERROR`, with the error.
- Whether the push succeeded.
