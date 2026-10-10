"""Learning journal for the learner agent.

Resources read and lessons learned are appended as markdown files under
``journal/`` next to the repo: one problem file per run plus an index
that /teach and /ask consult so teaching comes from what was learned.
"""

import os
import re
import time

JOURNAL_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                           "journal")
NOTES_DIR = os.path.join(JOURNAL_DIR, "notes")
INDEX = os.path.join(JOURNAL_DIR, "index.md")


def _ensure_dirs():
    os.makedirs(NOTES_DIR, exist_ok=True)


def _problem_path(slug):
    return os.path.join(JOURNAL_DIR, f"{slug}.md")


def entry_exists(slug):
    _ensure_dirs()
    return os.path.exists(_problem_path(slug))


def record_problem(slug, title, concept, provider, understanding, plan_text,
                   code, verdict, reflection, resources_used):
    """Write/overwrite the journal file for one problem run."""
    _ensure_dirs()
    stamp = time.strftime("%Y-%m-%d %H:%M")
    lines = [
        f"# {title} — {slug}",
        "",
        f"*{stamp} · concept `{concept}` · brain: {provider or 'offline'}*",
        "",
        "## Understanding (in my own words)",
        "", understanding or "—", "",
        "## Plan",
        "", plan_text or "—", "",
        "## Final code",
        "", "```c", code or "// (never produced)", "```", "",
        "## Verdict",
        "", verdict or "—", "",
        "## Resources I consulted",
        "",
    ]
    for r in resources_used or []:
        lines.append(f"- {r}")
    if not resources_used:
        lines.append("- (none — I solved it or failed on my own)")
    lines += ["", "## What I learned / teach-back", "", reflection or "—", ""]
    with open(_problem_path(slug), "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))
    _update_index(title, slug, concept)
    return os.path.relpath(_problem_path(slug), os.path.dirname(JOURNAL_DIR))


def record_note(name, title, url, summary):
    """Save a digest of one resource page the agent read."""
    _ensure_dirs()
    safe = re.sub(r"[^a-z0-9-]+", "", name.lower().replace(" ", "-"))[:60] or "note"
    path = os.path.join(NOTES_DIR, f"{safe}.md")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(f"# {title}\n\n*Source: {url}*\n\n{summary}\n")
    return safe


def _update_index(title, slug, concept):
    marker = f"- [{title}]({slug}.md) — `{concept}`"
    try:
        with open(INDEX, "r", encoding="utf-8") as fh:
            content = fh.read()
    except OSError:
        content = "# Journal index\n\nSolved & studied problems, roadmap order.\n"
    if slug in content:
        return
    content = content.rstrip() + "\n" + marker + "\n"
    with open(INDEX, "w", encoding="utf-8") as fh:
        fh.write(content)


def load_context(max_chars=6000):
    """Concatenate the whole journal as teach-back context for the brain."""
    _ensure_dirs()
    chunks = []
    # index first for a map of the territory
    for path in (INDEX, *sorted(
            (os.path.join(JOURNAL_DIR, f) for f in os.listdir(JOURNAL_DIR)
             if f.endswith(".md") and f != "index.md"),
            key=os.path.getmtime, reverse=True)):
        try:
            with open(path, "r", encoding="utf-8") as fh:
                chunks.append(fh.read())
        except OSError:
            continue
        if sum(len(c) for c in chunks) > max_chars:
            break
    return "\n\n---\n\n".join(chunks)[:max_chars]


def problem_count():
    try:
        return sum(1 for f in os.listdir(JOURNAL_DIR)
                   if f.endswith(".md") and f != "index.md")
    except OSError:
        return 0
