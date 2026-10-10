"""Teach-back chat: /teach and /quizme for the human.

The agent re-teaches from its journal. /quizme generates a multiple-choice
question about what it studied, then grades your reply locally (by letter,
number, or matching option text — same normalization style as grader.py).
"""

import difflib
import re

from . import brain, journal


def _print_reply(reply, provider):
    if reply:
        print()
        print(reply)
        if provider == "cloud":
            print("\n  (cloud brain)")
        print()
    else:
        print("\nNo brain reachable (ollama not running, no cloud key set).")
        print("Start ollama: `ollama serve && ollama pull llama3`\n")


def teach(topic=""):
    journal_doc = journal.load_context()
    if len(journal_doc.strip()) < 80:
        print("Journal is empty. Run /study first — I can only teach what I learned.")
        return
    prompt = (
        "Teach what you learned from the journal below"
        + (f", focusing on the topic '{topic}'" if topic else " today")
        + ". Use beginner-friendly language, one core idea at a time, "
        "with a tiny C example where helpful. Under 220 words.\n\nJournal:\n"
        + journal_doc
    )
    reply, provider = brain.think([{"role": "user", "content": prompt}])
    _print_reply(reply, provider)


def quizme(topic=""):
    journal_doc = journal.load_context()
    if len(journal_doc.strip()) < 80:
        print("Journal is empty. Run /study first — quiz comes from what I learned.")
        return
    reply, provider = brain.quiz_me(journal_doc, topic)
    if not reply:
        _print_reply(None, None)
        return
    try:
        question, options, answer, why = _parse_quiz(reply)
    except Exception:
        question, options, answer, why = None, {}, None, ""
    if question and answer in options:
        print()
        print(question)
        for k in "ABCD":
            if k in options:
                print(f"   {k}) {options[k]}")
        got = input("\nYour answer (A-D): ").strip().upper()[:1]
        if _correct(got, answer, options):
            print(f"✔ Correct. {why}")
        else:
            print(f"✘ It was {answer}. {why}")
    else:
        # brain made soup; show raw reply as teaching instead
        print("\n" + reply + "\n")


def _parse_quiz(reply):
    """Parse the QUESTION/A-D/ANSWER/WHY block the brain was asked for.

    Options use 'A) ...' (no colon) while QUESTION/ANSWER/WHY use ':',
    so each format gets its own matcher.
    """
    question = answer = why = None
    options = {}
    for line in reply.splitlines():
        ls = line.strip()
        m = re.match(r"question\s*[::]\s*(.+)", ls, re.I)
        if m:
            question = m.group(1)
        m = re.match(r"([A-D])[).]\s*(\S.+)", ls)
        if m:
            options[m.group(1)] = m.group(2)
        m = re.match(r"answer\s*[::]\s*([A-D])", ls, re.I)
        if m:
            answer = m.group(1).upper()
        m = re.match(r"why\s*[::]\s*(.+)", ls, re.I)
        if m:
            why = m.group(1)
    return question, options, answer, why


def _correct(got, answer, options):
    if not got:
        return False
    if got == answer:
        return True
    if got.isdigit():
        n = int(got)
        return 1 <= n <= 4 and "ABCD"[n - 1] == answer
    # accept option text too, with grader-style fuzz
    want = re.sub(r"[\W_]", "", (options[answer] or "").strip().lower())
    given = re.sub(r"[\W_]", "", got.lower())
    if not given:
        return False
    return given == want or difflib.SequenceMatcher(None, given, want).ratio() >= 0.8
