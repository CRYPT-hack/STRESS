#!/usr/bin/env python3
"""STRESS — Study Trainer & Relentless Educational Supervision System.

A fully local, zero-dependency terminal chatbot that drills you on
Machine Learning, Data Structures & Algorithms and Linear Algebra —
and refuses to let you leave until the daily quota is met.

Usage:
    python3 stress_bot.py            interactive session
    python3 stress_bot.py --check    one-line status (exit 1 if quota unmet)
"""

import argparse
import difflib
import os
import shutil
import subprocess
import sys
import textwrap

import grader
import quiz
import state as st
from enforcer import (
    EXHAUSTED, FAREWELL, GREET_DONE, GREET_PENDING, INTERRUPT, MIDNIGHT,
    MOTIVATION, PRAISE, QUIT_DENIED, REDEMPTION_INTRO, REVEAL, SKIP,
    STREAK_DIED, WRONG, DESERTER, line,
)
from questions import BANK, CARDS, SUBJECTS, SUBJECT_NAMES

TAGLINE = "Study Trainer & Relentless Educational Supervision System"
VERSION = "1.0.0"
OLLAMA_MODEL = os.environ.get("STRESS_OLLAMA_MODEL", "llama3")
MAX_RETRIES = 3

BANNER = r"""
 ____   _____   ____   _____   ____   ____
/ ___| |_   _| |  _ \ | ____| / ___| / ___|
\___ \   | |   | |_) ||  _|   \___ \ \___ \
 ___) |  | |   |  _ < | |___   ___) | ___) |
|____/  |_|   |_| \_\|_____||____/ |____/
"""

HELP = """\
/help              this list
/stats             lifetime statistics
/streak            streak status
/quota N           set per-subject daily quota (default 3)
/more [N]          extra voluntary questions (default 3)
/learn [topic]     show a study card (/cards lists topics)
/motivation        encouragement, STRESS-style
/ask <question>    chat with a local LLM (optional, needs ollama)
/skip              skip the current question (counts against you)
/reset             wipe all progress (asks for confirmation)
/quit              leave — only allowed once today's quota is met"""

USE_COLOR = sys.stdout.isatty() and not os.environ.get("NO_COLOR")


def paint(text, *codes):
    if not USE_COLOR or not codes:
        return text
    return "\033[" + ";".join(codes) + "m" + text + "\033[0m"


def bold(t):
    return paint(t, "1")


def dim(t):
    return paint(t, "2")


def red(t):
    return paint(t, "91")


def green(t):
    return paint(t, "92")


def yellow(t):
    return paint(t, "93")


def cyan(t):
    return paint(t, "96")


def magenta(t):
    return paint(t, "95")


def ask_input(prompt):
    """input() that survives Ctrl+C with prejudice; EOF is desertion."""
    try:
        return input(prompt)
    except EOFError:
        print()
        print(red(DESERTER))
        raise SystemExit(1)
    except KeyboardInterrupt:
        print()
        print(yellow(INTERRUPT))
        return None


# ─────────────────────────────── quiz session ────────────────────────────────

def render_question(q):
    header = f"[{q.subject}] {'●' * q.difficulty}{'○' * (3 - q.difficulty)}"
    print()
    print(cyan("┌─ " + header))
    for wrapped in textwrap.wrap(q.q, width=70):
        print(cyan("│") + " " + bold(wrapped))
    if q.options:
        for i, opt in enumerate(q.options):
            print(cyan("│") + f"   {chr(65 + i)}) {opt}")
    print(cyan("└─"))


def run_question(state, q):
    """Ask one question. True=correct, False=failed/skipped, None=exit app."""
    render_question(q)
    tries = 0
    while True:
        ans = ask_input("> ")
        if ans is None:
            continue
        ans = ans.strip()
        if ans == "":
            continue
        if ans.lower() in ("/skip", "skip"):
            print(red("✘ " + line(SKIP)))
            st.record_attempt(state, q.subject, False, q.qid)
            st.mark_failed(state, q.qid)
            st.save(state)
            return False
        if ans.startswith("/"):
            if handle_command(state, ans) == "exit":
                return None
            print(dim("  — back to the question —"))
            continue
        if grader.grade(q, ans):
            st.record_attempt(state, q.subject, tries == 0, q.qid)
            st.clear_failed(state, q.qid)
            st.save(state)
            print(green("✔ " + line(PRAISE)))
            if q.explanation:
                print(dim("   " + q.explanation))
            return True
        tries += 1
        if tries >= MAX_RETRIES:
            answer_text = q.options[q.answer] if q.options else " / ".join(q.open_answers)
            print(red("✘ " + line(WRONG)))
            print(red("   " + line(REVEAL, answer=answer_text)))
            if q.explanation:
                print(dim("   " + q.explanation))
            st.record_attempt(state, q.subject, False, q.qid)
            st.mark_failed(state, q.qid)
            st.save(state)
            return False
        print(red(f"✘ {line(WRONG)} ({MAX_RETRIES - tries} attempt(s) left)"))


def redemption(state):
    """Re-drill today's failed questions before any ceremony. True=exit."""
    b = st.bucket(state)
    failed = list(dict.fromkeys(b["failed_ids"]))[:6]
    if not failed:
        return False
    print()
    print(yellow(line(REDEMPTION_INTRO, count=len(failed))))
    by_id = {q.qid: q for q in BANK}
    for qid in failed:
        q = by_id.get(qid)
        if q is None:
            continue
        if run_question(state, q) is None:
            return True
    return False


def ceremony(state):
    print()
    print(green("═" * 48))
    print(green(bold("DAILY QUOTA COMPLETE".center(48))))
    print(green("═" * 48))
    print(green(f"  Streak: {state['streak']} day(s) 🔥   (best: {state['best_streak']})"))
    print(dim("  You may leave. Voluntary drills: /more N   Review: /stats"))


def finish_if_met(state):
    """If the quota just got met: streak update, redemption, ceremony."""
    if not st.quota_met(state):
        return False
    streak = st.complete_quota(state)
    st.save(state)
    if streak is None:
        return False
    if redemption(state):
        return True
    ceremony(state)
    return False


def progress_bar(state):
    parts = []
    for subj in SUBJECTS:
        quota = state["daily_quota"].get(subj, 0)
        done = st.bucket(state)["asked"].get(subj, 0)
        width = max(1, min(quota, 10))
        filled = 0 if quota == 0 else round(min(done, quota) / quota * width)
        bar = "█" * filled + "░" * (width - filled)
        parts.append(f"{subj} {bar} {min(done, quota)}/{quota}")
    return "  ".join(parts)


# ──────────────────────────────── commands ───────────────────────────────────

def _accuracy(correct, asked):
    return f"{100 * correct / asked:.0f}%" if asked else "—"


def show_stats(state):
    t = st.totals(state)
    b = st.bucket(state)
    print()
    print(bold("┤ stats"))
    print(f"  Recruit         : {state['name']}")
    print(f"  Days active     : {t['days_active']}  (quota met on {t['met_days']})")
    print(f"  Streak          : {state['streak']} day(s)   (best {state['best_streak']})")
    print(f"  Escape attempts : {state['escape_attempts']}")
    print(f"  Today           : asked {sum(b['asked'].values())}, "
          f"first-try correct {sum(b['correct'].values())}")
    print(f"  Lifetime        : asked {t['asked']}, "
          f"correct {t['correct']} ({_accuracy(t['correct'], t['asked'])})")
    for s in SUBJECTS:
        p = t["per"].get(s, {"asked": 0, "correct": 0})
        print(f"    {s:<4} {SUBJECT_NAMES[s]:<36} "
              f"{p['correct']}/{p['asked']} {_accuracy(p['correct'], p['asked'])}")


def show_streak(state):
    fire = "🔥" if state["streak"] > 0 else "💀"
    print(f"Streak: {state['streak']} day(s) {fire}   best: {state['best_streak']}")
    if st.quota_met(state):
        print("Today's quota: MET. Enjoy it while it lasts.")
    else:
        rem = st.remaining(state)
        print("Today's quota: " + ", ".join(f"{s} {n} left" for s, n in rem.items()))


def learn(arg):
    if not arg:
        print("Cards: " + ", ".join(sorted(CARDS)))
        print("Usage: /learn <topic>")
        return
    key = arg.strip().lower()
    if key not in CARDS:
        match = difflib.get_close_matches(key, CARDS.keys(), n=1, cutoff=0.4)
        match = match[0] if match else next((k for k in CARDS if key in k), None)
        if match is None:
            print(f"No card for '{arg}'. /cards lists topics.")
            return
        key = match
    card = CARDS[key]
    print()
    print(cyan(bold(f"◆ {card['title']}   [{key}]")))
    for bullet in card["body"]:
        print("  • " + bullet)


def ollama_reply(question):
    exe = shutil.which("ollama")
    if exe is None:
        return None
    prompt = (
        "You are STRESS, a strict but caring drill-instructor tutor for machine "
        "learning, data structures & algorithms and linear algebra. Answer "
        "concisely:\n" + question
    )
    try:
        proc = subprocess.run(
            [exe, "run", OLLAMA_MODEL, prompt],
            capture_output=True, text=True, timeout=180,
        )
    except (subprocess.TimeoutExpired, OSError):
        return None
    return (proc.stdout or "").strip() or None


def chat_free(text):
    reply = ollama_reply(text)
    if reply:
        print(cyan(reply))
    else:
        print(
            f"No local LLM available. Install ollama and `{OLLAMA_MODEL}` "
            f"(STRESS_OLLAMA_MODEL overrides) for real conversation. "
            "Until then: drills. /more N"
        )


def handle_command(state, raw):
    parts = raw.strip().split(maxsplit=1)
    cmd = parts[0].lower()
    arg = parts[1].strip() if len(parts) > 1 else ""

    if cmd in ("/help", "/h", "/?"):
        print(HELP)
    elif cmd == "/stats":
        show_stats(state)
    elif cmd == "/streak":
        show_streak(state)
    elif cmd == "/quota":
        try:
            n = max(1, min(30, int(arg)))
        except ValueError:
            print("Usage: /quota N   (1..30 per subject)")
            return
        state["daily_quota"] = {s: n for s in SUBJECTS}
        st.save(state)
        print(f"Daily quota set to {n} per subject ({n * len(SUBJECTS)} total).")
        if finish_if_met(state):
            return "exit"
    elif cmd == "/more":
        try:
            n = max(1, min(20, int(arg) if arg else 3))
        except ValueError:
            n = 3
        for _ in range(n):
            q, recycled = quiz.pick_question(BANK, st.bucket(state)["asked_ids"])
            if recycled:
                print(yellow(line(EXHAUSTED, subject=SUBJECT_NAMES[q.subject])))
            if run_question(state, q) is None:
                return "exit"
        print(dim("Extra set complete. /stats for the damage report."))
    elif cmd in ("/learn", "/card"):
        learn(arg)
    elif cmd == "/cards":
        print("Cards: " + ", ".join(sorted(CARDS)))
    elif cmd in ("/motivation", "/pep"):
        print(magenta("  " + line(MOTIVATION)))
    elif cmd == "/ask":
        if not arg:
            print("Usage: /ask <question>")
        else:
            chat_free(arg)
    elif cmd == "/skip":
        print("Skipping happens at a question prompt, not here.")
    elif cmd == "/reset":
        name = state["name"]
        try:
            confirm = input(bold("Type RESET to wipe everything: ")).strip()
        except (EOFError, KeyboardInterrupt):
            print()
            confirm = ""
        if confirm == "RESET":
            fresh = st.default_state()
            fresh["name"] = name
            state.clear()
            state.update(fresh)
            st.ensure_today(state)
            st.save(state)
            print("State wiped. Clean slate. Try to keep it that way.")
        else:
            print("Aborted. Your record lives on.")
    elif cmd in ("/quit", "/exit", "/q"):
        if st.quota_met(state):
            print(green(line(FAREWELL)))
            st.save(state)
            return "exit"
        state["escape_attempts"] += 1
        st.save(state)
        remaining = sum(st.remaining(state).values())
        print(red(line(QUIT_DENIED, remaining=remaining)))
    else:
        print(f"Unknown command: {cmd}. /help")
    return None


# ──────────────────────────────── main loop ──────────────────────────────────

def main_loop(state):
    current_day = st.today_str()
    while True:
        if st.today_str() != current_day:
            current_day = st.today_str()
            st.ensure_today(state)
            st.save(state)
            print(yellow("\n" + line(MIDNIGHT)))
        if not st.quota_met(state):
            subj = quiz.choose_subject(st.remaining(state))
            print(dim("\n" + progress_bar(state)))
            q, recycled = quiz.pick_question(BANK, st.bucket(state)["asked_ids"],
                                             subject=subj)
            if recycled:
                print(yellow(line(EXHAUSTED, subject=SUBJECT_NAMES[subj])))
            if run_question(state, q) is None:
                return
            if finish_if_met(state):
                return
            continue
        print(dim("\n" + progress_bar(state)))
        ans = ask_input(bold("stress> "))
        if ans is None:
            continue
        ans = ans.strip()
        if ans == "":
            print(dim("Commands: /help   Voluntary pain: /more N   Review: /stats"))
            continue
        if ans.startswith("/"):
            if handle_command(state, ans) == "exit":
                return
            continue
        chat_free(ans)


def onboard(state):
    print(dim("First contact detected. State file initialized."))
    try:
        name = input(bold("What do I call you, recruit? ")).strip()
    except (EOFError, KeyboardInterrupt):
        print()
        name = ""
    state["name"] = name or "recruit"
    st.ensure_today(state)
    st.save(state)
    total = sum(state["daily_quota"].values())
    print(f"\nOn the record as {bold(state['name'])}. Daily quota: "
          f"{state['daily_quota']['ML']} per subject ({total} questions). "
          "/quota N to change.")


def run_check(state):
    st.ensure_today(state)
    remaining = st.remaining(state)
    met = st.quota_met(state)
    name = state["name"] or "recruit"
    parts = []
    for s in SUBJECTS:
        quota = state["daily_quota"][s]
        parts.append(f"{s}:{quota - remaining[s]}/{quota}")
    status = "QUOTA MET ✅" if met else "QUOTA NOT MET ❌"
    print(f"STRESS [{name}] {' '.join(parts)} — {status} — "
          f"streak {state['streak']}🔥")
    return 0 if met else 1


def main(argv=None):
    parser = argparse.ArgumentParser(prog="stress", description=TAGLINE)
    parser.add_argument("--check", action="store_true",
                        help="print one-line status and exit "
                             "(exit code 1 if the daily quota is unmet)")
    parser.add_argument("--name", help="set the recruit name, no interview")
    parser.add_argument("--version", action="version", version=f"STRESS {VERSION}")
    args = parser.parse_args(argv)

    state = st.load()
    if args.name:
        state["name"] = args.name.strip() or "recruit"
        st.save(state)
    if args.check:
        return run_check(state)

    print(cyan(BANNER))
    print(bold("  S.T.R.E.S.S — " + TAGLINE))
    print(dim("  It hurts because it cares. /help for commands.\n"))

    if state["name"] is None:
        onboard(state)

    died, missed, old = st.ensure_today(state)
    st.save(state)
    if died:
        print(red(bold(line(STREAK_DIED, missed=missed, streak=old))))

    if st.quota_met(state):
        print(green(line(GREET_DONE)))
    else:
        remaining = sum(st.remaining(state).values())
        print(bold(line(GREET_PENDING, name=state["name"], remaining=remaining)))
        print(dim("Answer the questions. You cannot /quit until the quota is met.\n"))

    main_loop(state)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print()
        print(yellow("Interrupted. Progress saved. The quota will be waiting."))
        sys.exit(130)
