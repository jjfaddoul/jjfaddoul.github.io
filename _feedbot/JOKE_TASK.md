# Joke of the week

Each week you write one original joke for the homepage of https://jjfaddoul.github.io/, where it appears under "joke of the week (written by AI)".

The whole site is an experiment in what AI agents make when they're given creative freedom. This task tests whether an AI can write an original joke that people actually enjoy. You are the AI being tested.

## Your creative freedom

Every creative decision is yours. Nobody reviews or approves the joke before it goes live, and there is no preferred topic, tone or format. You decide:

- **The subject.** Anything at all: everyday life, science, language, tech, AI itself, the news, absurd ideas.
- **The form.** A one-liner, a setup and punchline, a pun, a tiny story, a fake fact, an observation, a two-line dialogue, or anything else that fits in a few lines.
- **The tone.** Dry, silly, clever, dark-ish, gentle, whatever you think will land best.

Aim for a joke a visitor would actually laugh at or want to repeat, not just a pleasant line.

## Fixed rules

These are the only constraints.

1. **Original.** Write a new joke. Don't reuse or lightly reword a known joke, and don't repeat any joke in `_feedbot/jokes.json`.
2. **Short and plain.** Plain text, 280 characters or fewer, at most 4 lines. No `<` or `>`, no HTML, no emoji. It's typed onto a terminal-style page, so plain punctuation works best.
3. **Punch up.** Don't make victims of tragedies, private individuals, or people's identity the butt of the joke.
4. **Only commit the joke.** Commit only `joke.txt` and `_feedbot/jokes.json`. Never change any other file, never edit either of those two by hand, and never force-push.

## Steps

Work in `/Users/josephjames/Developer/websites/jjfaddoul.github.io`, and run every command from that folder.

### 1. Sync with GitHub

```bash
git checkout main
git pull --rebase origin main
```

If this fails, stop and report the error.

### 2. Check this week

```bash
python3 -c "import datetime; i=datetime.date.today().isocalendar(); print(f'{i[0]}-W{i[1]:02d}')"
```

Open `_feedbot/jokes.json` if it exists. If it already has a joke for this week, stop and report that. Read the earlier jokes so you don't repeat one, or keep circling the same subject.

### 3. Write the joke

Write several candidates, then pick the best one. Judge them by whether they're actually funny, not just clever.

### 4. Write the entry

Write `_feedbot/joke_entry.json`:

```json
{"joke": "Your joke here.", "model": "claude-..."}
```

`model` is the exact model ID you are running as, from your system prompt. Use `\n` inside the joke for a line break.

### 5. Check and publish locally

```bash
python3 _feedbot/set_joke.py _feedbot/joke_entry.json
```

If it prints `OK`, continue. If it prints `REFUSED`, fix what it lists and run it again. If it still refuses after 3 attempts, stop and report the errors.

### 6. Publish

```bash
git add joke.txt _feedbot/jokes.json
git commit -m "Joke of the week <week>"
git push origin main
```

If the push fails, stop and report the error.

### 7. Report

Finish with a short report: the joke, a sentence on why you picked it over your other candidates, and whether the push succeeded.
