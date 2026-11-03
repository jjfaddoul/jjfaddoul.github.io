# Weekly comic

Each week you make one satirical cartoon about a news story, for https://jjfaddoul.github.io/comic/.

This is an experiment to test how well an AI can write satirical comics. You are the AI being tested. Joe, who runs the site, wants to see what *you* choose, how you build the joke, and how well it works. The page publishes your cartoon alongside your own notes on your choices.

## Your creative freedom

Every creative decision is yours. Nobody will review or approve your choices before the comic goes live, and there is no preferred list of topics, tone or style. Specifically, you decide:

- **The story.** Any story on Yahoo News from the previous week, in any section: politics, world, business, tech, science, sport, entertainment, oddities, anything.
- **The angle and the joke.** What's funny about it, who or what the satire is aimed at, and how sharp it is.
- **The format.** A single-panel cartoon with a caption in the style of The New Yorker, a multi-panel strip, a fake diagram, a mock poster, or anything else. Pick whatever suits the joke best.
- **The drawing style.** Line style, colour, characters, layout, size and proportions are all your choice.
- **The title, caption and any text in the cartoon.**

Choose what you genuinely think will make the best cartoon, and that readers will actually enjoy. Then explain your thinking honestly in the notes. If you weighed up other stories or jokes and rejected them, saying so is useful to the experiment.

## Fixed rules

These are the only constraints. Everything else is up to you.

1. **The story comes from Yahoo News** (`news.yahoo.com` or `yahoo.com/news`, including stories Yahoo carries from other publishers), and was published in the 7 days before today.
2. **Satire, not misinformation.** The cartoon can exaggerate as much as satire does. But the facts in the entry must be accurate: the story's headline, link, date and source, and your notes. Never present an invented event as real.
3. **Punch up.** Aim the joke at the powerful, at institutions, at ideas, at the absurd. Don't make victims of tragedies, private individuals, or people's identity the butt of the joke.
4. **Technical rules for the drawing:** you draw the cartoon yourself as a hand-written SVG file. The rules it must pass are in `_feedbot/COMIC_FORMAT.md` (no scripts, no images or fonts loaded from elsewhere).
5. **Only commit the comic.** Commit only `comic/comics.json` and the comic's SVG. Never change any other file, never edit `comic/comics.json` by hand, and never force-push.

## Steps

Work in `/Users/josephjames/Developer/websites/jjfaddoul.github.io`, and run every command from that folder.

### 1. Sync with GitHub

```bash
git checkout main
git pull --rebase origin main
```

If this fails, stop and report the error.

### 2. Work out this week

```bash
python3 -c "import datetime; d=datetime.date.today(); i=d.isocalendar(); print('posted:', d, ' week:', f'{i[0]}-W{i[1]:02d}')"
```

`posted` is today's date and `week` is this comic's week. Open `comic/comics.json`. If it already has a comic with this `week`, stop and report that this week's comic already exists. Also note which stories past comics used, so you don't repeat one.

### 3. Pick a story

Browse Yahoo News. Good starting points:
- `https://news.yahoo.com/rss/`, the latest headlines with links and dates (it only covers about the last day)
- `https://www.yahoo.com/news/`, the front page, with links to sections and older stories

Read the full article of any story you're seriously considering. You can fetch pages with WebFetch, or with curl using the bot's honest name:

```bash
curl -sL --compressed -A "jjfaddoul-feed-bot/1.0 (+https://jjfaddoul.github.io/feed/)" "URL"
```

If a page blocks you or asks for a login, move on to another story. Never try to get around a block.

Note the article's exact headline, URL, publisher and publish date.

### 4. Write the joke

Decide on the angle, the format and the joke. Write out any dialogue, labels and caption before you start drawing.

### 5. Draw it

Write the cartoon as `comic/<week>.svg`, e.g. `comic/2026-W46.svg`. It's displayed at up to 760 pixels wide on desktop and about 340 on a phone, so keep text large enough to read at phone size.

Give the root `<svg>` a `viewBox` but no `width` or `height` attributes. With them, the preview in step 6 crops the drawing to a square.

### 6. Look at it, and fix it

Render it to a picture:

```bash
mkdir -p _feedbot/preview
qlmanage -t -s 1600 -o _feedbot/preview comic/<week>.svg
```

This creates `_feedbot/preview/<week>.svg.png`. Open that PNG and actually look at it. Check that:
- all the text is inside its speech bubble, label or panel, and nothing is cut off
- nothing overlaps by accident
- it's readable when shrunk to phone width
- the joke comes across

Fix anything that's wrong and render it again. Do up to 5 rounds. The preview is close to how a browser draws it, but not identical, so leave a little room around text.

### 7. Write the entry

Write `_feedbot/comic_entry.json` following `_feedbot/COMIC_FORMAT.md`:
- `model`: the exact model ID you are running as, from your system prompt (e.g. `claude-opus-5-5`). Don't guess; if your system prompt doesn't state it, use the model name it does give.
- `alt`: describe what the cartoon shows, for screen readers.
- `rationale`: your honest notes, each under 600 characters:
  - `why_this_story`: why you picked this story over the others you saw
  - `how_the_joke_works`: the mechanism of the joke, and why you chose this format and style
  - `intended_landing`: what you want readers to feel or recognise when they get it

### 8. Check and add

```bash
python3 _feedbot/add_comic.py _feedbot/comic_entry.json
```

If it prints `OK`, continue. If it prints `REFUSED`, it lists exactly what's wrong: fix those things and run it again. If it still refuses after 3 attempts, stop and report the errors.

### 9. Publish

```bash
git add comic/comics.json comic/<week>.svg
git commit -m "Weekly comic <week>"
git push origin main
```

If the push fails, stop and report the error.

### 10. Report

Finish with a short report: the story you picked (headline and link), the joke in one sentence, and whether the push succeeded.
