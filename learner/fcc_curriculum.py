"""freeCodeCamp curriculum: challenge lists pulled straight from FCC's
Gatsby `page-data.json` (public, no auth, same JSON the browser loads).

Usage:
    python3 -m learner.fcc_curriculum js | html

Tracks (key -> superblock slug + display name):
    js   javascript-algorithms-and-data-structures  299 challenges
    html 2022/responsive-web-design                1037 steps/quizzes
    py   scientific-computing-with-python          legacy
"""

import json
import os
import urllib.request

CACHE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                         ".fcc-curriculum")
FCC = "https://www.freecodecamp.org"

TRACKS = {
    "js":  "javascript-algorithms-and-data-structures",
    "html": "2022/responsive-web-design",
    "py":  "scientific-computing-with-python",
}

# challengeType 1 = classic code challenge, 0 = step-by-step project,
# 5 = quiz, 6 = exam, 14 = exam. Solvable by the bot:
SOLVABLE_TYPES = {0, 1}


def _headers():
    return {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}


def _fetch_json(url, timeout=30):
    req = urllib.request.Request(url, headers=_headers())
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def superblock_slugs(track):
    """Cache key includes the track's superblock path parts."""
    return TRACKS[track].replace("/", "-")


def list_challenges(track, force=False):
    """Return the ordered solvable challenges of a track.

    Each entry: dict(slug, title, challengeType, block, id).
    Ordered as FCC orders them (already the curriculum order).
    """
    os.makedirs(CACHE_DIR, exist_ok=True)
    superblock = TRACKS[track]
    cache = os.path.join(CACHE_DIR, f"{superblock.replace('/', '-')}.json")

    if not force and os.path.exists(cache):
        try:
            with open(cache, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass

    url = f"{FCC}/page-data/learn/{superblock}/page-data.json"
    data = _fetch_json(url)
    nodes = data["result"]["data"]["allChallengeNode"]["nodes"]
    prefix = f"/learn/{superblock}/"
    items = []
    for node in nodes:
        c = node.get("challenge") or {}
        slug = (c.get("fields") or {}).get("slug", "")
        if not slug.startswith(prefix):
            continue  # sitemap page also lists redirects from other blocks
        if c.get("challengeType") not in SOLVABLE_TYPES:
            continue
        if c.get("translationPending"):
            continue
        items.append({
            "slug": slug,
            "title": c.get("title") or "",
            "challengeType": c.get("challengeType"),
            "block": c.get("block") or "",
            "id": c.get("id") or "",
        })
    items.sort(key=lambda x: slug)  # stable order per block
    with open(cache, "w", encoding="utf-8") as f:
        json.dump(items, f)
    return items


# ── your-account progress ───────────────────────────────────────────────────

def profile_url(fcc_id):
    """The /fcc-<uuid> profile page slugs are the public username."""
    return f"{FCC}/fcc-{fcc_id}" if "fcc-" not in fcc_id.lower() else f"{FCC}/{fcc_id}"


# first bot-runnable block per track, in curriculum order
START_BLOCKS = {
    "js":   "basic-javascript",
    "html": "learn-html-by-building-a-cat-photo-app",
    "py":   "python-for-everybody",
}


def next_unfinished(track, done_slugs, start_block=None):
    """First challenge in the track whose slug is not in done_slugs."""
    start_block = start_block or START_BLOCKS[track]
    bank = list_challenges(track)
    in_block = [c for c in bank if c["block"] == start_block]
    ordered = in_block + [c for c in bank if c["block"] != start_block]
    for c in ordered:
        if c["slug"] not in done_slugs:
            return c
    return None


def count_remaining(track, done_slugs):
    return sum(1 for c in list_challenges(track) if c["slug"] not in done_slugs)


if __name__ == "__main__":
    import sys
    for which in (sys.argv[1:] or ["js", "html"]):
        chs = list_challenges(which, force="--fresh" in sys.argv)
        print(f"[{which}] {len(chs)} solvable challenges")
        for c in chs[:3]:
            print("   ", c["slug"], "—", c["title"])
