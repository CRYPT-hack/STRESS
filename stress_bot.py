#!/usr/bin/env python3
"""STRESS — Study Trainer & Relentless Educational Supervision System.

A fully local, zero-dependency terminal chatbot that drills you on
Machine Learning, Data Structures & Algorithms and Linear Algebra — and 
refuses to let you leave until the daily quota is met.

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

try:
    import learner.chat
    import learner.fcc_driver
    import learner.session
    LEARNER_OK = True
except ImportError as _le:
    LEARNER_OK = False
    LEARNER_WARN = str(_le)

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
VERSION = "1.2.0"
OLLAMA_MODEL = os.environ.get("STRESS_OLLAMA_MODEL", "llama3")
MAX_RETRIES = 3

BANNER = r"""
 ____   _____   ____   _____   ____   ____
/ ___| |_   _| |  _ \ | ____| / ___| / ___|
\___ \   | |   | |_) ||  _|   \___ \ \___ \
 ___) |  | |   |  _ < | |___   ___) | ___)
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
/quit              leave — only allowed once today's quota is met
/study [N]         learner agent solves next NeetCode problems in a visible
                   browser (auto-runs; you press Submit) — needs ollama
/freecode [N]      agent SOLVES freeCodeCamp HTML + JS challenges directly,
                   two parallel browser sessions, auto-Submit on pass —
                   needs ollama; first run asks you to log in to FCC
/freecode-100      same but 100 challenges each on JS + HTML, stops on its own
/fcc [N]           same as /freecode
/free [N]          same as /freecode
/teach [topic]     the agent teaches what it learned from its journal
/quizme [topic]    the agent quizzes YOU on what it learned
/learner           learner progress: problems done, concepts covered
"""

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
            print(green("✔ correct") + "  (" + str(q.options[tries]) + ")")
            return True
        tries += 1
        print(red("✘ " + line(WRONG, attempt=tries)))
        if tries >= 2:
            print(dim("  give up: " + q.answer_hint()))
            break
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
        if grader.grade(q, ans):
            st.record_attempt(state, q.subject, tries == 0, q.qid)
            st.clear_failed(state, q.qid)
            st.save(state)
            print(green("✔ correct") + "  (after " + str(tries) + " tries)")
            return True
        print(red("✘ " + line(WRONG, attempt=tries + 1)))
        break

    print(dim("  give up: " + q.answer_hint()))
    print(dim("  next time it's yours."))
    st.record_attempt(state, q.subject, False, q.qid)
    st.mark_failed(state, q.qid)
    st.save(state)
    return False


# ─────────────────────────────── main loop ────────────────────────────────

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
                print(yellow(line(EXHAUSTED, subject=SUBJECT_NAMES[quiz.choose_subject(st.remaining(state))])))
            if run_question(state, q) is None:
                return
            if finish_if_met(state):
                return
            continue
        if finish_if_met(state):
            return "exit"
    elif cmd in ("/learn", "/card"):
        learn(arg)
    elif cmd == "/cards":
        learn("")
    elif cmd in ("/motivation", "/pep"):
        print(green(line(MOTIVATION[0])))
        print(dim("and " + line(MOTIVATION[1])))
    elif cmd == "/ask":
        ollama_reply(arg)
    elif cmd == "/skip":
        print(red("✘ " + line(SKIP)))
        st.record_attempt(state, "ML", False, "skip")
        st.save(state)
    elif cmd == "/reset":
        print()
        print(red(bold("reset is permanent.")))
        try:
            confirm = ask_input("type 'yes' to confirm, anything else cancels: ")
        except (EOFError, KeyboardInterrupt):
            print()
            return
        if confirm.strip().lower() == "yes":
            state.clear()
            st.ensure_today(state)
            st.save(state)
            print("State wiped. Clean slate. Try to keep it that way.")
        else:
            print("Aborted. Your record lives on.")
    elif cmd in ("/study", "/s"):
        if not LEARNER_OK:
            print(f"Learner module failed to import: {LEARNER_WARN}")
            return
        try:
            n = max(1, min(5, int(arg) if arg else 1))
        except ValueError:
            n = 1
        print(dim("Opening LeetCode in a visible browser. Watch, don't help."))
        learner.session.study(n, state)
        st.save(state)
    elif cmd in ("/freecode", "/fcc", "/free"):
        if not LEARNER_OK:
            print(f"Learner module failed to import: {LEARNER_WARN}")
            return
        try:
            n = max(1, min(20, int(arg) if arg else 4))
        except ValueError:
            n = 4
        tracks = ("js", "html") if "html" in arg or "both" in arg else ("js", "html")
        if arg.startswith("js"):
            tracks = ("js",)
        elif arg.startswith("html"):
            tracks = ("html",)
        print(dim(f"Opening freeCodeCamp. Tracks: {', '.join(tracks)}. "
                  "Solve → Run the Tests → auto-Submit."))
        learner.fcc_driver.run_session(state, n, tracks=tracks)
        st.save(state)
        fcc = state.get("fcc", {}).get("done", {})
        print(green(f"  FCC done so far — js: {len(fcc.get('js', []))}, "
                    f"html: {len(fcc.get('html', []))}"))
    elif cmd in ("/freecode-100", "/fcc-100", "/free-100"):
        if not LEARNER_OK:
            print(f"Learner module failed to import: {LEARNER_WARN}")
            return
        tracks = ("js", "html") if "html" in arg or "both" in arg else ("js", "html")
        if arg.startswith("js"):
            tracks = ("js",)
        elif arg.startswith("html"):
            tracks = ("html",)
        n = 100
        print(dim(f"Opening freeCodeCamp — 100 challenges each on {', '.join(tracks)}. "
                  "Stops on its own when done; press Ctrl+C to interrupt."))
        try:
            learner.fcc_driver.run_session(state, n, tracks=tracks)
        except KeyboardInterrupt:
            print()
            print(yellow("Paused by you (Ctrl+C). Progress saved."))
        st.save(state)
        fcc = state.get("fcc", {}).get("done", {})
        print(green(f"  FCC done — js: {len(fcc.get('js', []))}, "
                    f"html: {len(fcc.get('html', []))}"))
    elif cmd in ("/teach", "/t"):
        if LEARNER_OK:
            learner.chat.teach(arg)
    elif cmd in ("/quizme", "/quizme"):
        if LEARNER_OK:
            learner.chat.quizme(arg)
    elif cmd == "/learner":
        if LEARNER_OK:
            show_learner(state)
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


def show_stats(state):
    print()
    print(bold("┤ lifetime quiz stats"))
    q = state.get("quiz", {})
    if not q:
        print(dim("none yet — start drilling."))
        return
    asked = q.get("asked_total", 0)
    correct = q.get("correct_total", 0)
    print(f"  asked        : {asked}")
    print(f"  correct      : {correct}")
    print(f"  accuracy     : {_accuracy(correct, asked)}")
    print(f"  final streak : {state.get('streak', 0)}🔥")
    per = q.get("per_subject", {})
    if per:
        print(bold("  per subject"))
        for s in SUBJECTS:
            p = per.get(s, {})
            print(f"    {s:<4} {SUBJECT_NAMES[s]:<36} "
                  + f"{p.get('correct', 0)}/{p.get('asked', 0)} "
                  + f"({_accuracy(p.get('correct', 0), p.get('asked', 0))})")
    print("  top the SDF table first — it uses everything else.")


def show_learner(state):
    from learner import session as _s
    learner = state.get("learner", {}) or {}
    done = learner.get("done_problems", [])
    n_done, n_total = _s.progress(done)
    print()
    print(bold("┤ learner agent"))
    print(f"  Problems in curriculum : {n_done}/{n_total}")
    if done:
        print(f"  Latest                 : {done[-1]}")
    print(f"  Study journal          : journal/index.md  ({_s.problem_count()} entries)")
    c = learner.get("concepts", {})
    if c:
        top = sorted(c.items(), key=lambda kv: -kv[1])[:6]
        print("  Concepts covered       : " + ", ".join(f"{k}×{v}" for k, v in top))
    fcc = state.get("fcc", {}).get("done", {})
    print(bold("┤ fcc agent"))
    print(f"  freeCodeCamp solved    : js {len(fcc.get('js', []))} · html {len(fcc.get('html', []))}")
    print("  To run FCC mode        : /freecode [N]   (default 4; 'js' or 'html' in arg limits track)")
    print("  To run 100 challenges  : /freecode-100")
    print("  To train more          : /study [N]   To be taught: /teach")


def show_streak(state):
    s = state.get("streak", 0)
    print()
    print(bold("┤ streak"))
    print(f"  current   : {s} day{'s' if s != 1 else ''}🔥" if s else "  current   : broken")
    print(f"  best      : {state.get('best_streak', 0)} day{'s' if state.get('best_streak', 0) != 1 else ''}")
    if s:
        print(dim(f"  keep it alive — every day matters. tomorrow's quota waits."))


def learn(arg):
    from learner import session as _s
    cards = _s.C_CARDS
    if not arg:
        print()
        print(bold("┤ study cards"))
        for key, card in sorted(cards.items()):
            print(f"  /learn {key:<12} {card['title']}")
        return
    if arg not in cards:
        print(dim("no such card. /cards to list them."))
        return
    card = cards[arg]
    print()
    print(bold(card["title"]))
    for b in card["body"]:
        print(dim("  " + b))


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


def _accuracy(correct, asked):
    return "n/a" if not asked else f"{correct / asked:.0%}"


def progress_bar(state):
    asked = state.get("asked_total", 0)
    width = 20
    filled = int(width * asked / max(asked, 1))
    return "[" + "█" * filled + "░" * (width - filled) + f"] {asked}"


def finish_if_met(state):
    if st.quota_met(state):
        print()
        print(green(line(PRAISE)))
        state["finished_today"] = True
        st.save(state)
        return True
    return False


# ─────────────────────────────── reset ───────────────────────────────────────


def reset(state):
    print()
    print(red(bold("reset is permanent.")))
    try:
        confirm = ask_input("type 'yes' to confirm, anything else cancels: ")
    except (EOFError, KeyboardInterrupt):
        print()
        return
    if confirm.strip().lower() == "yes":
        state.clear()
        st.ensure_today(state)
        st.save(state)
        print("State wiped. Clean slate. Try to keep it that way.")
    else:
        print("Aborted. Your record lives on.")


def show_stats(state):
    print()
    print(bold("┤ lifetime quiz stats"))
    q = state.get("quiz", {})
    if not q:
        print(dim("none yet — start drilling."))
        return
    asked = q.get("asked_total", 0)
    correct = q.get("correct_total", 0)
    print(f"  asked        : {asked}")
    print(f"  correct      : {correct}")
    print(f"  accuracy     : {_accuracy(correct, asked)}")
    print(f"  final streak : {state.get('streak', 0)}🔥")
    per = q.get("per_subject", {})
    if per:
        print(bold("  per subject"))
        for s in SUBJECTS:
            p = per.get(s, {})
            print(f"    {s:<4} {SUBJECT_NAMES[s]:<36} "
                  + f"{p.get('correct', 0)}/{p.get('asked', 0)} "
                  + f"({_accuracy(p.get('correct', 0), p.get('asked', 0))})")
    print("  top the SDF table first — it uses everything else.")


def show_learner(state):
    from learner import session as _s
    learner = state.get("learner", {}) or {}
    done = learner.get("done_problems", [])
    n_done, n_total = _s.progress(done)
    print()
    print(bold("┤ learner agent"))
    print(f"  Problems in curriculum : {n_done}/{n_total}")
    if done:
        print(f"  Latest                 : {done[-1]}")
    print(f"  Study journal          : journal/index.md  ({_s.problem_count()} entries)")
    c = learner.get("concepts", {})
    if c:
        top = sorted(c.items(), key=lambda kv: -kv[1])[:6]
        print("  Concepts covered       : " + ", ".join(f"{k}×{v}" for k, v in top))
    fcc = state.get("fcc", {}).get("done", {})
    print(bold("┤ fcc agent"))
    print(f"  freeCodeCamp solved    : js {len(fcc.get('js', []))} · html {len(fcc.get('html', []))}")
    print("  To run FCC mode        : /freecode [N]   (default 4; 'js' or 'html' in arg limits track)")
    print("  To run 100 challenges  : /freecode-100")
    print("  To train more          : /study [N]   To be taught: /teach")


def show_streak(state):
    s = state.get("streak", 0)
    print()
    print(bold("┤ streak"))
    print(f"  current   : {s} day{'s' if s != 1 else ''}🔥" if s else "  current   : broken")
    print(f"  best      : {state.get('best_streak', 0)} day{'s' if state.get('best_streak', 0) != 1 else ''}")
    if s:
        print(dim(f"  keep it alive — every day matters. tomorrow's quota waits."))


def learn(arg):
    from learner import session as _s
    cards = _s.C_CARDS
    if not arg:
        print()
        print(bold("┤ study cards"))
        for key, card in sorted(cards.items()):
            print(f"  /learn {key:<12} {card['title']}")
        return
    if arg not in cards:
        print(dim("no such card. /cards to list them."))
        return
    card = cards[arg]
    print()
    print(bold(card["title"]))
    for b in card["body"]:
        print(dim("  " + b))


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


def _accuracy(correct, asked):
    return "n/a" if not asked else f"{correct / asked:.0%}"


def progress_bar(state):
    asked = state.get("asked_total", 0)
    width = 20
    filled = int(width * asked / max(asked, 1))
    return "[" + "█" * filled + "░" * (width - filled) + f"] {asked}"


def finish_if_met(state):
    if st.quota_met(state):
        print()
        print(green(line(PRAISE)))
        state["finished_today"] = True
        st.save(state)
        return True
    return False


# ─────────────────────────────── main loop ────────────────────────────────


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
            print(f"Usage: /quota N   (1..30 per subject)")
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
                print(yellow(line(EXHAUSTED, subject=SUBJECT_NAMES[quiz.choose_subject(st.remaining(state))])))
            if run_question(state, q) is None:
                return
            if finish_if_met(state):
                return
            continue
        if finish_if_met(state):
            return "exit"
    elif cmd in ("/learn", "/card"):
        learn(arg)
    elif cmd == "/cards":
        learn("")
    elif cmd in ("/motivation", "/pep"):
        print(green(line(MOTIVATION[0])))
        print(dim("and " + line(MOTIVATION[1])))
    elif cmd == "/ask":
        ollama_reply(arg)
    elif cmd == "/skip":
        print(red("✘ " + line(SKIP)))
        st.record_attempt(state, "ML", False, "skip")
        st.save(state)
    elif cmd == "/reset":
        print()
        print(red(bold("reset is permanent.")))
        try:
            confirm = ask_input("type 'yes' to confirm, anything else cancels: ")
        except (EOFError, KeyboardInterrupt):
            print()
            return
        if confirm.strip().lower() == "yes":
            state.clear()
            st.ensure_today(state)
            st.save(state)
            print("State wiped. Clean slate. Try to keep it that way.")
        else:
            print("Aborted. Your record lives on.")
    elif cmd in ("/study", "/s"):
        if not LEARNER_OK:
            print(f"Learner module failed to import: {LEARNER_WARN}")
            return
        try:
            n = max(1, min(5, int(arg) if arg else 1))
        except ValueError:
            n = 1
        print(dim("Opening LeetCode in a visible browser. Watch, don't help."))
        learner.session.study(n, state)
        st.save(state)
    elif cmd in ("/freecode", "/fcc", "/free"):
        if not LEARNER_OK:
            print(f"Learner module failed to import: {LEARNER_WARN}")
            return
        try:
            n = max(1, min(20, int(arg) if arg else 4))
        except ValueError:
            n = 4
        tracks = ("js", "html") if "html" in arg or "both" in arg else ("js", "html")
        if arg.startswith("js"):
            tracks = ("js",)
        elif arg.startswith("html"):
            tracks = ("html",)
        print(dim(f"Opening freeCodeCamp. Tracks: {', '.join(tracks)}. "
                  "Solve → Run the Tests → auto-Submit."))
        learner.fcc_driver.run_session(state, n, tracks=tracks)
        st.save(state)
        fcc = state.get("fcc", {}).get("done", {})
        print(green(f"  FCC done so far — js: {len(fcc.get('js', []))}, "
                    f"html: {len(fcc.get('html', []))}"))
    elif cmd in ("/freecode-100", "/fcc-100", "/free-100"):
        if not LEARNER_OK:
            print(f"Learner module failed to import: {LEARNER_WARN}")
            return
        tracks = ("js", "html") if "html" in arg or "both" in arg else ("js", "html")
        if arg.startswith("js"):
            tracks = ("js",)
        elif arg.startswith("html"):
            tracks = ("html",)
        n = 100
        print(dim(f"Opening freeCodeCamp — 100 challenges each on {', '.join(tracks)}. "
                  "Stops on its own when done; press Ctrl+C to interrupt."))
        try:
            learner.fcc_driver.run_session(state, n, tracks=tracks)
        except KeyboardInterrupt:
            print()
            print(yellow("Paused by you (Ctrl+C). Progress saved."))
        st.save(state)
        fcc = state.get("fcc", {}).get("done", {})
        print(green(f"  FCC done — js: {len(fcc.get('js', []))}, "
                    f"html: {len(fcc.get('html', []))}"))
    elif cmd in ("/teach", "/t"):
        if LEARNER_OK:
            learner.chat.teach(arg)
    elif cmd in ("/quizme", "/quizme"):
        if LEARNER_OK:
            learner.chat.quizme(arg)
    elif cmd == "/learner":
        if LEARNER_OK:
            show_learner(state)
    elif cmd in ("/quit", "/exit", "/q"):
        if st.quota_met(state):
            print(green(line(FAREWELL)))
            st.save(state)
            return "exit"


def show_stats(state):
    print()
    print(bold("┤ lifetime quiz stats"))
    q = state.get("quiz", {})
    if not q:
        print(dim("none yet — start drilling."))
        return
    asked = q.get("asked_total", 0)
    correct = q.get("correct_total", 0)
    print(f"  asked        : {asked}")
    print(f"  correct      : {correct}")
    print(f"  accuracy     : {_accuracy(correct, asked)}")
    print(f"  final streak : {state.get('streak', 0)}🔥")
    per = q.get("per_subject", {})
    if per:
        print(bold("  per subject"))
        for s in SUBJECTS:
            p = per.get(s, {})
            print(f"    {s:<4} {SUBJECT_NAMES[s]:<36} "
                  + f"{p.get('correct', 0)}/{p.get('asked', 0)} "
                  + f"({_accuracy(p.get('correct', 0), p.get('asked', 0))})")
    print("  top the SDF table first — it uses everything else.")


def show_learner(state):
    from learner import session as _s
    learner = state.get("learner", {}) or {}
    done = learner.get("done_problems", [])
    n_done, n_total = _s.progress(done)
    print()
    print(bold("┤ learner agent"))
    print(f"  Problems in curriculum : {n_done}/{n_total}")
    if done:
        print(f"  Latest                 : {done[-1]}")
    print(f"  Study journal          : journal/index.md  ({_s.problem_count()} entries)")
    c = learner.get("concepts", {})
    if c:
        top = sorted(c.items(), key=lambda kv: -kv[1])[:6]
        print("  Concepts covered       : " + ", ".join(f"{k}×{v}" for k, v in top))
    fcc = state.get("fcc", {}).get("done", {})
    print(bold("┤ fcc agent"))
    print(f"  freeCodeCamp solved    : js {len(fcc.get('js', []))} · html {len(fcc.get('html', []))}")
    print("  To run FCC mode        : /freecode [N]   (default 4; 'js' or 'html' in arg limits track)")
    print("  To run 100 challenges  : /freecode-100")
    print("  To train more          : /study [N]   To be taught: /teach")


def show_streak(state):
    s = state.get("streak", 0)
    print()
    print(bold("┤ streak"))
    print(f"  current   : {s} day{'s' if s != 1 else ''}🔥" if s else "  current   : broken")
    print(f"  best      : {state.get('best_streak', 0)} day{'s' if state.get('best_streak', 0) != 1 else ''}")
    if s:
        print(dim(f"  keep it alive — every day matters. tomorrow's quota waits."))


def learn(arg):
    from learner import session as _s
    cards = _s.C_CARDS
    if not arg:
        print()
        print(bold("┤ study cards"))
        for key, card in sorted(cards.items()):
            print(f"  /learn {key:<12} {card['title']}")
        return
    if arg not in cards:
        print(dim("no such card. /cards to list them."))
        return
    card = cards[arg]
    print()
    print(bold(card["title"]))
    for b in card["body"]:
        print(dim("  " + b))


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


def _accuracy(correct, asked):
    return "n/a" if not asked else f"{correct / asked:.0%}"


def progress_bar(state):
    asked = state.get("asked_total", 0)
    width = 20
    filled = int(width * asked / max(asked, 1))
    return "[" + "█" * filled + "░" * (width - filled) + f"] {asked}"


def finish_if_met(state):
    if st.quota_met(state):
        print()
        print(green(line(PRAISE)))
        state["finished_today"] = True
        st.save(state)
        return True
    return False


def show_stats(state):
    print()
    print(bold("┤ lifetime quiz stats"))
    q = state.get("quiz", {})
    if not q:
        print(dim("none yet — start drilling."))
        return
    asked = q.get("asked_total", 0)
    correct = q.get("correct_total", 0)
    print(f"  asked        : {asked}")
    print(f"  correct      : {correct}")
    print(f"  accuracy     : {_accuracy(correct, asked)}")
    print(f"  final streak : {state.get('streak', 0)}🔥")
    per = q.get("per_subject", {})
    if per:
        print(bold("  per subject"))
        for s in SUBJECTS:
            p = per.get(s, {})
            print(f"    {s:<4} {SUBJECT_NAMES[s]:<36} "
                  + f"{p.get('correct', 0)}/{p.get('asked', 0)} "
                  + f"({_accuracy(p.get('correct', 0), p.get('asked', 0))})")
    print("  top the SDF table first — it uses everything else.")


def show_learner(state):
    from learner import session as _s
    learner = state.get("learner", {}) or {}
    done = learner.get("done_problems", [])
    n_done, n_total = _s.progress(done)
    print()
    print(bold("┤ learner agent"))
    print(f"  Problems in curriculum : {n_done}/{n_total}")
    if done:
        print(f"  Latest                 : {done[-1]}")
    print(f"  Study journal          : journal/index.md  ({_s.problem_count()} entries)")
    c = learner.get("concepts", {})
    if c:
        top = sorted(c.items(), key=lambda kv: -kv[1])[:6]
        print("  Concepts covered       : " + ", ".join(f"{k}×{v}" for k, v in top))
    fcc = state.get("fcc", {}).get("done", {})
    print(bold("┤ fcc agent"))
    print(f"  freeCodeCamp solved    : js {len(fcc.get('js', []))} · html {len(fcc.get('html', []))}")
    print("  To run FCC mode        : /freecode [N]   (default 4; 'js' or 'html' in arg limits track)")
    print("  To run 100 challenges  : /freecode-100")
    print("  To train more          : /study [N]   To be taught: /teach")


def show_streak(state):
    s = state.get("streak", 0)
    print()
    print(bold("┤ streak"))
    print(f"  current   : {s} day{'s' if s != 1 else ''}🔥" if s else "  current   : broken")
    print(f"  best      : {state.get('best_streak', 0)} day{'s' if state.get('best_streak', 0) != 1 else ''}")
    if s:
        print(dim(f"  keep it alive — every day matters. tomorrow's quota waits."))


def learn(arg):
    from learner import session as _s
    cards = _s.C_CARDS
    if not arg:
        print()
        print(bold("┤ study cards"))
        for key, card in sorted(cards.items()):
            print(f"  /learn {key:<12} {card['title']}")
        return
    if arg not in cards:
        print(dim("no such card. /cards to list them."))
        return
    card = cards[arg]
    print()
    print(bold(card["title"]))
    for b in card["body"]:
        print(dim("  " + b))


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


def _accuracy(correct, asked):
    return "n/a" if not asked else f"{correct / asked:.0%}"


def progress_bar(state):
    asked = state.get("asked_total", 0)
    width = 20
    filled = int(width * asked / max(asked, 1))
    return "[" + "█" * filled + "░" * (width - filled) + f"] {asked}"


def finish_if_met(state):
    if st.quota_met(state):
        print()
        print(green(line(PRAISE)))
        state["finished_today"] = True
        st.save(state)
        return True
    return False


def show_stats(state):
    print()
    print(bold("┤ lifetime quiz stats"))
    q = state.get("quiz", {})
    if not q:
        print(dim("none yet — start drilling."))
        return
    asked = q.get("asked_total", 0)
    correct = q.get("correct_total", 0)
    print(f"  asked        : {asked}")
    print(f"  correct      : {correct}")
    print(f"  accuracy     : {_accuracy(correct, asked)}")
    print(f"  final streak : {state.get('streak', 0)}🔥")
    per = q.get("per_subject", {})
    if per:
        print(bold("  per subject"))
        for s in SUBJECTS:
            p = per.get(s, {})
            print(f"    {s:<4} {SUBJECT_NAMES[s]:<36} "
                  + f"{p.get('correct', 0)}/{p.get('asked', 0)} "
                  + f"({_accuracy(p.get('correct', 0), p.get('asked', 0))})")
    print("  top the SDF table first — it uses everything else.")


def show_learner(state):
    from learner import session as _s
    learner = state.get("learner", {}) or {}
    done = learner.get("done_problems", [])
    n_done, n_total = _s.progress(done)
    print()
    print(bold("┤ learner agent"))
    print(f"  Problems in curriculum : {n_done}/{n_total}")
    if done:
        print(f"  Latest                 : {done[-1]}")
    print(f"  Study journal          : journal/index.md  ({_s.problem_count()} entries)")
    c = learner.get("concepts", {})
    if c:
        top = sorted(c.items(), key=lambda kv: -kv[1])[:6]
        print("  Concepts covered       : " + ", ".join(f"{k}×{v}" for k, v in top))
    fcc = state.get("fcc", {}).get("done", {})
    print(bold("┤ fcc agent"))
    print(f"  freeCodeCamp solved    : js {len(fcc.get('js', []))} · html {len(fcc.get('html', []))}")
    print("  To run FCC mode        : /freecode [N]   (default 4; 'js' or 'html' in arg limits track)")
    print("  To run 100 challenges  : /freecode-100")
    print("  To train more          : /study [N]   To be taught: /teach")


def show_streak(state):
    s = state.get("streak", 0)
    print()
    print(bold("┤ streak"))
    print(f"  current   : {s} day{'s' if s != 1 else ''}🔥" if s else "  current   : broken")
    print(f"  best      : {state.get('best_streak', 0)} day{'s' if state.get('best_streak', 0) != 1 else ''}")
    if s:
        print(dim(f"  keep it alive — every day matters. tomorrow's quota waits."))


def learn(arg):
    from learner import session as _s
    cards = _s.C_CARDS
    if not arg:
        print()
        print(bold("┤ study cards"))
        for key, card in sorted(cards.items()):
            print(f"  /learn {key:<12} {card['title']}")
        return
    if arg not in cards:
        print(dim("no such card. /cards to list them."))
        return
    card = cards[arg]
    print()
    print(bold(card["title"]))
    for b in card["body"]:
        print(dim("  " + b))
