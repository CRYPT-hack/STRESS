"""Question selection for STRESS."""

import random


def choose_subject(remaining):
    """Pick the subject furthest from its quota; None when all are met."""
    live = [s for s, n in remaining.items() if n > 0]
    if not live:
        return None
    fewest = min(remaining[s] for s in live)
    return random.choice([s for s in live if remaining[s] == fewest])


def pick_question(bank, asked_ids, subject=None):
    """Return (question, recycled).

    Avoids questions already asked today; when a subject's pool runs dry
    it recycles (recycled=True) rather than blocking the session.
    """
    if subject is not None:
        pool = [q for q in bank if q.subject == subject]
        fresh = [q for q in pool if q.qid not in asked_ids]
        if fresh:
            return random.choice(fresh), False
        return random.choice(pool), True
    fresh = [q for q in bank if q.qid not in asked_ids]
    if fresh:
        return random.choice(fresh), False
    return random.choice(list(bank)), True
