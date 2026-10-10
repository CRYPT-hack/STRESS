# STRESS Learner Agent — Startup Guide

Your terminal bot that trains a second bot — a beginner student who learns
DSA in C by working real LeetCode problems **in a visible browser window**,
researching free resources when stuck, journaling what it learns, and then
teaching YOU back.

Everything is local: Python + Playwright + Ollama. No accounts, no cloud,
no API keys (cloud brain optional).

---

## 1. One-time setup (already done ✓)

Skip this section unless setting up on a fresh machine.

| Step | Command | Status on this machine |
|---|---|---|
| Python 3.8+ | `python --version` | ✓ 3.14 |
| Playwright | `pip install playwright` | ✓ |
| Chromium for Playwright | `python -m playwright install chromium` | ✓ |
| Ollama | installer from ollama.com | ✓ 0.40.2 |
| llama3 model (~4.7 GB) | `ollama pull llama3` | ✓ |
| Code | `git clone https://github.com/CRYPT-hack/STRESS.git` | ✓ at `C:\Users\Shobhit Rai\STRESS` |

Handy check that everything is alive:

```powershell
ollama --version                       # 0.40.2 expected
curl http://localhost:11434/api/tags   # shows llama3 model
```

## 2. Start every session

```powershell
cd C:\Users\Shobhit Rai\STRESS
python stress_bot.py
```

You land in the normal STRESS drill bot (quota, streaks, guilt). The
learner commands work from the same prompt:

```
stress> /study
```

## 3. The four commands that matter

| Command | What happens |
|---|---|
| `/study` | Opens a **visible browser window**. The agent opens the next problem on the [NeetCode 150 roadmap](learner/curriculum.py), reads the problem, admits what it doesn't know, reads free resources (NeetCode / GeeksforGeeks / Beej's C Guide / freeCodeCamp), writes a plan, writes C code, types it into the LeetCode editor, clicks **Run**. When the visible tests pass it stops and waits for **you** to click **Submit**. |
| `/study 3` | Three problems in one sitting. |
| `/teach` | The agent re-teaches what it learned, straight from its journal. |
| `/quizme` | The agent generates a multiple-choice question about what it studied and grades your answer. |
| `/learner` | Progress dashboard: problems done, concepts covered, journal size. |

Plus the classics: `/stats`, `/streak`, `/learn c-pointers`, `/ask <question>`,
`/help`. `/learn` also has beginner cards: `c-basics`, `c-io`, `c-pointers`,
`c-memory`, `dsa-roadmap`.

## 4. What a `/study` session looks like

Terminal narrates each step with a speaker tag:

```
[agent]  Reading problem...
[me]     wait, what is a hash map again? ...
[reading] Hashing in Data Structure · https://www.geeksforgeeks.org/hashing-in-data-structure/
[learned] A hash map turns a key into an index so lookup is O(1)...
[plan]   1. Count frequencies in a dict. 2. ...
[run]    Runtime: 40 ms, beats 62%. Your input: [2,7,11,15] ...
```

Meanwhile a Chromium window is open on your screen doing the actual
clicking. You are just watching a nervous first-year student work.

When it stops:

```
─── [REVIEW] Code is in the editor. Please click SUBMIT yourself, ───
      then come back and press <Enter> here (or 'n' to skip).

   submitted? <Enter>=yes / n=skip:
```

- Press **Enter** after you've clicked Submit on the site.
- Press **n** to skip — the attempt is journaled as unsubmitted.

## 5. The rule the agent never breaks

**The agent only clicks Run, never Submit.** You always press the final
button on leetcode.com yourself. This keeps automation inside LeetCode's
acceptable-use line — the agent is your study mirror, not a submission
farm.

## 6. Where the learning lives

| Location | Contents |
|---|---|
| `journal/<slug>.md` | One file per problem: understanding, plan, final code, verdict, resources consulted, teach-back summary |
| `journal/notes/*.md` | Digest of every resource page the agent read |
| `journal/index.md` | Running list, roadmap order |
| `stress_state.json` | `learner` section: done_problems, attempts, concepts (gitignored, machine-local) |

Reading `journal/two-sum.md` after a session = free revision notes,
in beginner voice.

## 7. Troubleshooting

| Symptom | Fix |
|---|---|
| ` Stress … can't open file` | You're in the wrong folder — `cd C:\Users\Shobhit Rai\STRESS` first. |
| `No brain: ollama isn't running` | Start Ollama app or `ollama serve`, then retry. |
| Agent opens browser but can't read the page | LeetCode changed markup; LeetCode may also wall some pages until you log in **inside the agent's browser window** (session persists in `.lc-profile/`). |
| `[browser] couldn't open browser (...playwright...)` | `pip install playwright` then `python -m playwright install chromium`. |
| Learner state got weird | Delete `stress_state.json` — bot rebuilds; journal files remain and still teach. |
| Update after I improve the code | `git pull` inside the STRESS folder. |

## 8. Optional: stronger brain

Local llama3 is enough for Easy problems and honest confusion. For Medium+
problems set a cloud fallback before starting the bot:

```powershell
$env:STRESS_CLOUD_BASE_URL = "https://api.openai.com/v1"
$env:STRESS_CLOUD_API_KEY   = "sk-..."
$env:STRESS_CLOUD_MODEL     = "gpt-4o-mini"
python stress_bot.py
```

Nothing is sent anywhere unless you set those vars — ollama stays primary.
