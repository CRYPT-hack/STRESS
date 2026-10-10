# STRESS

**S**tudy **T**rainer & **R**elentless **E**ducational **S**upervision **S**ystem

A 100% local, zero-dependency terminal chatbot whose entire personality is:
*"You will study ML, DSA and Linear Algebra today, and you will like it."*

It quizzes you, tracks your streaks, guilt-trips you when you slack off,
and **refuses to let you quit the session until your daily quota is done**.
No accounts, no cloud, no API keys — just Python 3 and your conscience.

```
 ____   _____   ____   _____   ____   ____
/ ___| |_   _| |  _ \ | ____| / ___| / ___|
\___ \   | |   | |_) ||  _|   \___ \ \___ \
 ___) |  | |   |  _ < | |___   ___) | ___) |
|____/  |_|   |_| \_\|_____||____/ |____/
```

## Quick start

```bash
python3 stress_bot.py
```

That's it. Python ≥ 3.8, standard library only. Your progress is stored in
`stress_state.json` next to the script (gitignored — it never leaves your machine).

## How it forces you to study

- **Daily quota** — by default 3 questions *per subject* (ML, DSA, Linear
  Algebra = 9 total). Questions are multiple-choice or typed answers, graded
  locally with normalization + fuzzy matching, each with an explanation.
- **`/quit` is denied** until the quota is met. Every denied attempt is counted
  and shown back to you in `/stats` as *escape attempts*.
- **Ctrl+C gets lectured** and the session continues. EOF (Ctrl+D) lets you out,
  but the bot calls it desertion and your unfinished quota stays on the record.
- **Streaks die** — meet the quota daily to grow a streak. Skip a day and the
  next launch opens with an obituary for it.
- **Redemption round** — every question you fail or skip gets re-asked before
  the session can end. Fail it three times and the answer is revealed with an
  explanation, but it comes back.
- **No repeats per day** — questions already asked today aren't re-asked until
  the pool is exhausted.

## Commands

| Command | What it does |
|---|---|
| `/help` | list commands |
| `/stats` | lifetime + per-subject accuracy, days active, escape attempts |
| `/streak` | current and best streak, what's left today |
| `/quota N` | set per-subject daily quota (1–30) |
| `/more [N]` | voluntary extra questions after the quota (default 3) |
| `/learn [topic]` | study cards (`/cards` lists topics) |
| `/motivation` | a pep talk, drill-instructor flavored |
| `/ask <question>` | free chat via a local LLM (optional, see below) |
| `/skip` | skip the current question (counts against you, comes back later) |
| `/reset` | wipe all progress (requires typing RESET) |
| `/quit` | leave — only once today's quota is met |

## Make it hunt you (optional)

`--check` prints a one-line status and exits — non-zero if the quota is unmet:

```bash
$ python3 stress_bot.py --check
STRESS [crypt] ML:1/3 DSA:3/3 LA:0/3 — QUOTA NOT MET ❌ — streak 4🔥
```

Wire it into cron so it nags you all evening:

```cron
*/45 18-23 * * *  cd /path/to/STRESS && python3 stress_bot.py --check
```

Or into your shell prompt so every new terminal reminds you:

```bash
PS1='$(python3 /path/to/STRESS/stress_bot.py --check 2>/dev/null)\n'"$PS1"
```

## GRIM — the desktop reaper 👻

GRIM is a little grim reaper who **lives on your screen**: a transparent,
always-on-top sprite that roams around on its own, bobs as it walks, flips
direction, and periodically stops you with a speech-bubble quiz question.
Left-click him for a taunt, double-click for an instant quiz, right-click
for the menu (quiz now / voice / quit). Everything outside his sprite and
bubble is click-through — he never blocks your desktop.

His questions come from the same bank, and his answers feed the **same
state file**: quota, streak and redemption ledger are shared with the
terminal bot. Meet the daily quota entirely through the reaper if you like.

He also *speaks* through `speech-dispatcher` (`spd-say`), if present, in a
lowered voice. Silent on machines without it.

```bash
./grim.sh                 # normal haunting: a quiz every 4–9 minutes
./grim.sh --test          # rapid-fire demo (first quiz after 8s)
./grim.sh --no-voice      # silent mode
./grim.sh --size 260      # bigger reaper
./grim.sh --min-gap 1 --max-gap 3   # more aggressive
```

Flags: `--size` (sprite height px), `--min-gap`/`--max-gap` (minutes between
quizzes), `--speed`, `--no-voice`, `--test`. Quit via his right-click menu.

Under the hood: PyGObject/GTK3 over XWayland (`GDK_BACKEND=x11`) for free
positioning, a 32-bit ARGB window, X11 input masks for click-through, and
sprites built from `assets/source.webp` by `make_sprites.py` (checkerboard
knockout via border flood-fill with morphological closing, so hollow robes
stay solid). Auto-start on login: copy `grim.sh` into
`~/.config/autostart/` as a `.desktop` entry, or add it to your session.

## Optional: real conversation via a local LLM

If you have [ollama](https://ollama.com) installed, `/ask <question>` (and any
free text typed at the `stress>` prompt after your quota is met) is answered by
a local model. Nothing is sent anywhere.

```bash
ollama pull llama3                 # or any model
export STRESS_OLLAMA_MODEL=llama3  # default
```

Without ollama, the bot just tells you to get back to drills.

## LEARNER — the student agent on your screen 🧠

New in 1.1.0: STRESS trains a *second* bot — a beginner student who learns DSA
in C by working real LeetCode problems in a **visible browser window**, reading
free resources when stuck, and then teaching you back.

```bash
# one-time setup
pip install playwright
python -m playwright install chromium
ollama pull llama3   # the agent's brain (local only)
```

Run the interactive bot and:

```
/study             the agent opens leetcode.com on screen, reads the next
                   NeetCode-150 problem, confesses what it doesn't know,
                   reads NeetCode/GfG/Beej's Guide to fill gaps, writes C,
                   types it into the editor and clicks Run — then stops so
                   YOU press Submit (never auto-submitted)
/study 3           three problems in one sitting
/teach             the agent teaches you what it learned (from its journal)
/quizme            the agent quizzes YOU on what it studied
/learner           progress: problems done, concepts covered
```

Everything it learns is journaled to `journal/` as markdown — one file per
problem plus notes/ digests per resource read, indexed in `journal/index.md`.
`/ask` and the free-chat line stay available; set a cloud LLM with
`STRESS_CLOUD_BASE_URL` + `STRESS_CLOUD_API_KEY` (OpenAI-compatible) if the
local brain is too small.

Module layout: `learner/curriculum.py` (NeetCode 150 + C warm-up cards) ·
`learner/browser.py` (headed Playwright, persistent profile in `.lc-profile/`)
· `learner/brain.py` (ollama primary, cloud fallback) · `learner/research.py`
(curated free-resource registry: GfG, Beej, freeCodeCamp, NeetCode) ·
`learner/journal.py` · `learner/chat.py` · `learner/session.py` (the /study
driver).

## Add your own questions

Open `questions.py` and append to the bank — one line each:

```python
mcq("ML", "Your question?", ["Wrong", "Right", "Wrong", "Wrong"], 1,
    "Explanation shown after the answer.", difficulty=2)

openq("LA", "Compute det([[1, 2], [3, 4]]).", ["-2"],
      explanation="1·4 − 2·3 = −2.", difficulty=1)
```

Study cards live in the `CARDS` dict in the same file.

## Development

```bash
python3 -m unittest -v test_stress    # grader, streak math, quota logic, bank sanity
python3 -m unittest -v test_reaper    # sprite knockout, flip, reaper food
```

Layout: `stress_bot.py` (REPL + commands) · `questions.py` (bank + cards) ·
`grader.py` (answer grading) · `quiz.py` (selection) · `state.py` (persistence)
· `enforcer.py` (the attitude) · `reaper.py` + `grim.sh` (desktop reaper) ·
`make_sprites.py` + `assets/` (sprite pipeline) · `learner/` (the student
agent, see LEARNER above).

## License

MIT — see [LICENSE](LICENSE).
