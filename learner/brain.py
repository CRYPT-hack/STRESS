"""The learner's brain: local ollama primary, optional cloud LLM fallback.

All prompts are written to make the model play a *beginner student*:
it narrates confusion, reads resources, reasons step by step, and never
claims pre-existing expertise. Output goes to the terminal as narration.
"""

import json
import os
import subprocess
import urllib.request

OLLAMA_HOST = os.environ.get("STRESS_OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.environ.get("STRESS_OLLAMA_MODEL", "llama3")

CLOUD_BASE_URL = os.environ.get("STRESS_CLOUD_BASE_URL")   # e.g. https://api.openai.com/v1
CLOUD_API_KEY = os.environ.get("STRESS_CLOUD_API_KEY")
CLOUD_MODEL = os.environ.get("STRESS_CLOUD_MODEL", "gpt-4o-mini")

TIMEOUT = 180


def _verse(persona):
    return persona.startswith("strict")


PERSONA = (
    "You are a first-year engineering student learning data structures & "
    "algorithms in C. You know almost nothing yet and you are OK with that. "
    "You narrate your thinking out loud, in short lines. You admit confusion "
    "freely ('wait, what is a hash map again?'). You never pretend to already "
    "know the answer. When you have read learning material you use it, and "
    "you say which resource taught you. Keep answers under ~150 words unless "
    "writing code."
)

PERSONA_STRICT = (
    "You are STRESS, a strict drill-instructor tutor. Grade the student's "
    "understanding honestly. Keep answers under ~120 words."
)


def _ollama_chat(messages):
    body = json.dumps({
        "model": OLLAMA_MODEL,
        "messages": messages,
        "stream": False,
    }).encode()
    req = urllib.request.Request(
        OLLAMA_HOST + "/api/chat",
        data=body,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        data = json.loads(resp.read().decode())
    return (data.get("message") or {}).get("content", "").strip()


def _cloud_chat(messages):
    if not (CLOUD_BASE_URL and CLOUD_API_KEY):
        return None
    body = json.dumps({
        "model": CLOUD_MODEL,
        "messages": messages,
        "temperature": 0.4,
    }).encode()
    req = urllib.request.Request(
        CLOUD_BASE_URL.rstrip("/") + "/chat/completions",
        data=body,
        headers={
            "Content-Type": "application/json",
            "Authorization": "Bearer " + CLOUD_API_KEY,
        },
    )
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        data = json.loads(resp.read().decode())
    return (data["choices"][0]["message"]["content"]).strip()


def think(messages):
    """Send chat messages to ollama; fall back to cloud; None if both fail.

    `messages` is a list of {"role": ..., "content": ...} dicts. A system
    persona is prepended if the first message isn't already a system one.
    """
    if messages[0].get("role") != "system":
        messages = [{"role": "system", "content": PERSONA}, *messages]
    try:
        reply = _ollama_chat(messages)
        if reply:
            return reply, "ollama"
    except Exception:
        pass
    try:
        reply = _cloud_chat(messages)
        if reply:
            return reply, "cloud"
    except Exception:
        pass
    return None, None


# ── convenience wrappers, each returns (text, provider) ────────────────────

def understand(problem_text, prior_notes=""):
    user = (
        "A classmate handed me this problem statement. Explain what it is "
        "asking in my own words, and list what I need to relearn to even "
        "start. Problem:\n\n" + problem_text[:3000]
    )
    if prior_notes:
        user += "\n\nNotes I already have from earlier:\n" + prior_notes[:1500]
    return think([{"role": "user", "content": user}])


def read_resource(page_title, page_text, question):
    user = (
        f"I just read a page titled '{page_title}' while stuck on a problem.\n"
        f"My question: {question}\n\n"
        "Summarize, in a beginner voice, the ONE idea from this page that "
        "answers my question, plus any caveats. Quote the resource name.\n\n"
        "Page text:\n" + page_text[:6000]
    )
    return think([{"role": "user", "content": user}])


def plan(problem_text, understanding, resource_notes=""):
    user = (
        "Here is a problem I am working on:\n\n" + problem_text[:2500] +
        "\n\nMy rambling understanding so far:\n" + (understanding or "(none)")[:800]
    )
    if resource_notes:
        user += "\n\nWhat I learned from reading resources:\n" + resource_notes[:1500]
    user += (
        "\n\nNow plan an approach in numbered steps, beginner level, "
        " mentioning the DSA pattern by name. Do not write code yet."
    )
    return think([{"role": "user", "content": user}])


def write_code(plan_text, problem_text, stub, failing="", prior_notes=""):
    user = (
        "Problem:\n" + problem_text[:2000] +
        "\n\nPlan:\n" + (plan_text or "")[:1200] +
        "\n\nWrite ONLY the solution in C, following this exact signature/struct:\n"
        + stub[:800] +
        "\nRules: pure C (LeetCode C flavor), no extra main(), no printf, "
        "no commentary sentences inside the code, malloc allowed. "
        "Return JUST the code in a single ```c fenced block."
    )
    if failing:
        user += "\n\nPrevious attempt failed with:\n" + failing[:800]
    if prior_notes:
        user += "\n\nMy study notes so far:\n" + prior_notes[:1200]
    return think([{"role": "user", "content": user}])


def reflect(problem_text, attempts_summary, final_code):
    user = (
        "Reflection time. Problem I just worked on:\n" + problem_text[:1500] +
        "\n\nWhat I tried (summary):\n" + attempts_summary[:1500] +
        "\n\nWhere I ended up (code):\n```c\n" + (final_code or "(none)")[:1500] + "\n```"
        "\n\nTeach-back time: explain to a fellow student the core pattern, "
        "what I got wrong the first time, and the ONE C concept I learned. "
        "Be humble, be concrete, under 150 words."
    )
    return think([{"role": "user", "content": user}])


def verdict_interpret(result_text):
    user = (
        "LeetCode just gave me this result panel text: '"
        + result_text[:1200] + "'\n"
        "One short line: did it pass, and if not, what is the single most "
        "likely beginner reason?"
    )
    return think([{"role": "user", "content": user}])


def ask(tutor_context, question):
    """Answer a question as the *tutor*, grounded in what the agent learned."""
    user = (
        "You are speaking as the tutor now. Here is what you (as the "
        "student-agent) learned and journaled:\n" + tutor_context[:4000] +
        "\n\nThe student asks: " + question +
        "\nAnswer grounded in the journal above when possible; if the "
        "journal doesn't cover it, say so and answer from general knowledge, "
        "still beginner-friendly and short."
    )
    return think([
        {"role": "system", "content": PERSONA_STRICT},
        {"role": "user", "content": user},
    ])


def quiz_me(tutor_context, topic_hint=""):
    user = (
        "Based on this journal, generate ONE multiple-choice quiz question "
        "with 4 options (A-D) to test the student on the topic "
        f"'{topic_hint or 'whatever the journal covers'}'. "
        "Format exactly:\nQUESTION: <text>\nA) ...\nB) ...\nC) ...\nD) ...\n"
        "ANSWER: <letter>\nWHY: <one line>\n\nJournal:\n" + tutor_context[:4000]
    )
    return think([
        {"role": "system", "content": PERSONA_STRICT},
        {"role": "user", "content": user},
    ])


def extract_code(reply):
    """Pull the first ```c (or ``` fallback) fenced block out of a reply."""
    if not reply:
        return None
    for tag in ("c", "C", ""):
        marker = "```" + tag
        idx = reply.find(marker)
        if idx == -1:
            continue
        start = reply.find("\n", idx)
        if start == -1:
            continue
        end = reply.find("```", start + 1)
        if end == -1:
            continue
        return reply[start + 1:end].rstrip() + "\n"
    return None
