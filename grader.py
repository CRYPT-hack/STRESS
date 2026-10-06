"""Answer grading for STRESS.

Multiple choice accepts the letter (a/b/c/d), the number (1/2/3/4), or
the (approximately) matching option text. Open answers accept exact
normalized matches, numeric equivalence, close fuzzy matches, or the
presence of all required keywords.
"""

import difflib
import re

FUZZY_THRESHOLD = 0.80
_LETTERS = "abcdefg"


def _norm(text):
    """Lowercase, drop spacing and math noise so 'O(log n)' == 'ologn'."""
    text = str(text).strip().lower()
    text = re.sub(r"[\s_]+", "", text)
    text = re.sub(r"[\(\)\[\]\{\}\$]", "", text)
    text = text.rstrip(".,;:!?")
    return text


def _as_float(text):
    try:
        return float(text)
    except (TypeError, ValueError):
        return None


def grade(question, reply):
    """Return True if `reply` is an acceptable answer to `question`."""
    if reply is None:
        return False
    if question.options is not None:
        return _grade_choice(question, reply)
    return _grade_open(question, reply)


def _grade_choice(question, reply):
    r = re.sub(r"[^a-z0-9]", "", reply.strip().lower())
    if not r:
        return False
    if r.isdigit():
        n = int(r)
        return 1 <= n <= len(question.options) and n - 1 == question.answer
    if len(r) == 1 and r in _LETTERS[: len(question.options)]:
        return _LETTERS.index(r) == question.answer
    target = _norm(question.options[question.answer])
    given = _norm(reply)
    return given == target or (
        difflib.SequenceMatcher(None, given, target).ratio() >= FUZZY_THRESHOLD
    )


def _grade_open(question, reply):
    given = _norm(reply)
    if not given:
        return False
    given_num = _as_float(given)
    for accepted in question.open_answers:
        want = _norm(accepted)
        if given == want:
            return True
        if given_num is not None and _as_float(want) == given_num:
            return True
        if difflib.SequenceMatcher(None, given, want).ratio() >= FUZZY_THRESHOLD:
            return True
    if question.keywords:
        return all(_norm(k) in given for k in question.keywords)
    return False
