"""Persistent state for STRESS.

Everything lives in ``stress_state.json`` next to this file (gitignored).
Dates are stored as ISO strings so the file stays human-readable and
diff-friendly.
"""

import json
import os
import tempfile
from datetime import date, timedelta

STATE_VERSION = 1


def default_state():
    return {
        "version": STATE_VERSION,
        "name": None,
        "daily_quota": {"ML": 3, "DSA": 3, "LA": 3},
        "streak": 0,
        "best_streak": 0,
        "last_quota_date": None,
        "escape_attempts": 0,
        "days": {},  # date -> {asked, correct, quota_met, asked_ids, failed_ids}
    }


def state_path():
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "stress_state.json")


def load(path=None):
    path = path or state_path()
    state = default_state()
    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, json.JSONDecodeError):
        return state  # missing or corrupt -> fresh start, never crash
    if not isinstance(data, dict):
        return state
    for key, value in data.items():
        if key in state:
            state[key] = value
    return state


def save(state, path=None):
    path = path or state_path()
    directory = os.path.dirname(path)
    fd, tmp = tempfile.mkstemp(dir=directory, prefix=".stress_state_", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(state, fh, indent=2, sort_keys=True)
        os.replace(tmp, path)
    except BaseException:
        try:
            os.remove(tmp)
        except OSError:
            pass
        raise


def today_str():
    return date.today().isoformat()


def _parse_day(day):
    return date.fromisoformat(day) if day else None


def ensure_today(state, today=None):
    """Create today's bucket and expire a neglected streak.

    Returns (streak_died, missed_days, old_streak).
    """
    today = today or date.today()
    key = today.isoformat()
    days = state["days"]
    if key not in days:
        days[key] = {
            "asked": {},
            "correct": {},
            "quota_met": False,
            "asked_ids": [],
            "failed_ids": [],
        }
    last = _parse_day(state["last_quota_date"])
    if (
        last is not None
        and state["streak"] > 0
        and last != today
        and last != today - timedelta(days=1)
    ):
        died, missed, old = True, (today - last).days - 1, state["streak"]
        state["streak"] = 0
        return died, missed, old
    return False, 0, state["streak"]


def bucket(state, today=None):
    today = today or date.today()
    days = state["days"]
    key = today.isoformat()
    if key not in days:
        died, missed, old = ensure_today(state, today)
        # ensure_today only expires old streaks; the bucket now exists.
        assert key in days
    return days[key]


def asked_today(state, subject, today=None):
    return bucket(state, today)["asked"].get(subject, 0)


def record_attempt(state, subject, correct, question_id, today=None):
    b = bucket(state, today)
    b["asked"][subject] = b["asked"].get(subject, 0) + 1
    if correct:
        b["correct"][subject] = b["correct"].get(subject, 0) + 1
    if question_id and question_id not in b["asked_ids"]:
        b["asked_ids"].append(question_id)


def mark_failed(state, question_id, today=None):
    b = bucket(state, today)
    if question_id and question_id not in b["failed_ids"]:
        b["failed_ids"].append(question_id)


def clear_failed(state, question_id, today=None):
    b = bucket(state, today)
    if question_id in b["failed_ids"]:
        b["failed_ids"].remove(question_id)


def quota_met(state, today=None):
    b = bucket(state, today)
    return all(b["asked"].get(s, 0) >= n for s, n in state["daily_quota"].items())


def remaining(state, today=None):
    b = bucket(state, today)
    return {
        s: max(0, n - b["asked"].get(s, 0)) for s, n in state["daily_quota"].items()
    }


def complete_quota(state, today=None):
    """Flip today's quota to met and advance the streak.

    Returns the new streak, or None if it was already met earlier today.
    """
    today = today or date.today()
    b = bucket(state, today)
    if b.get("quota_met"):
        return None
    b["quota_met"] = True
    last = _parse_day(state["last_quota_date"])
    if last == today:
        state["streak"] = max(state["streak"], 1)
    elif last == today - timedelta(days=1):
        state["streak"] += 1
    else:
        state["streak"] = 1
    state["best_streak"] = max(state["best_streak"], state["streak"])
    state["last_quota_date"] = today.isoformat()
    return state["streak"]


def totals(state):
    asked = correct = 0
    per = {}
    for b in state["days"].values():
        for s, n in b.get("asked", {}).items():
            asked += n
            per.setdefault(s, {"asked": 0, "correct": 0})
            per[s]["asked"] += n
        for s, n in b.get("correct", {}).items():
            correct += n
            per.setdefault(s, {"asked": 0, "correct": 0})
            per[s]["correct"] += n
    return {
        "asked": asked,
        "correct": correct,
        "per": per,
        "days_active": len(state["days"]),
        "met_days": sum(1 for b in state["days"].values() if b.get("quota_met")),
    }
