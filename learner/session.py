"""The /study session: the learner agent's main work loop.

Flow per problem:
  1. Open LeetCode in the visible browser window.
  2. Read the problem statement.
  3. Confess confusion (brain), consult free resources, save notes.
  4. Plan → write C → type into the editor → click RUN (never SUBMIT).
  5. Read the verdict; when all visible tests pass, pause and let the
     human click Submit.
  6. Journal entry + state update.

The browser window is visible the whole time — the user watches the
agent learn. Terminal narrates each step so the user can follow live.
"""

import textwrap

from . import brain, browser, curriculum, journal, research


def _say(who, text, width=88):
    print(f"  \033[96m[{who}]\033[0m ", end="")
    print(textwrap.fill(text, width=width,
                        subsequent_indent=" " * (len(who) + 5)))


def warmup():
    """First-run C/DSP vocab priming, straight from the cards."""
    print("\n  \033[1;95m── Day zero: whatever 'C' is, I start from nothing ──\033[0m")
    for key in ("c-basics", "c-io", "c-pointers"):
        card = curriculum.C_CARDS[key]
        print(f"\n  ◆ {card['title']}")
        for b in card["body"]:
            print("     • " + b)
    print()
    return True


def study(N, state):
    """Run one study session of N problems (or until brain absent)."""
    learner = state.setdefault("learner", {})
    done = learner.get("done_problems", [])

    if not learner.get("warmup_done"):
        warmup()
        learner["warmup_done"] = True

    brain_reply, provider = brain.think([{"role": "user",
                                          "content": "Ready to study. Say yes in 5 words."}])
    if not brain_reply:
        print("\nNo brain: ollama isn't running and no cloud key is set.")
        print("  Install:    winget install ollama")
        print("  Then:       ollama pull llama3")
        print("  Or set env: STRESS_CLOUD_BASE_URL + STRESS_CLOUD_API_KEY")
        return False

    use_blind75 = False
    problems_run = 0
    for _ in range(N):
        problem = curriculum.next_problem(done, use_blind75=use_blind75)
        if problem is None:
            print("\nCurriculum complete. 150 problems. /teach to review.")
            break
        print(f"\n\033[1;95m══ Problem {problems_run + 1} of {min(N, 5)}: "
              f"{problem.title} \033[0m"
              f" \033[2m[{problem.category} · {problem.difficulty} · "
              f"{curriculum.progress(done)[0]}/{curriculum.progress(done)[1]}]\033[0m")
        if _work_problem(state, problem, provider):
            done.append(problem.slug)
            problems_run += 1
        else:
            learner["attempts"][problem.slug] = learner.get("attempts", {}).get(problem.slug, 0) + 1
            _say("agent", "I'm being honest — I'll come back to this one.")
        state["learner"]["done_problems"] = done
    return True


def _work_problem(state, problem, provider):
    learner = state.setdefault("learner", {})
    attempts = learner.setdefault("attempts", {})
    concepts = learner.setdefault("concepts", {})

    # browser + problem read
    problem_text = ""
    try:
        with browser.Browser() as b:
            page = b.open_problem(problem.slug)
            b.ensure_c_language(page)
            problem_text = b.problem_text(page)
            if not problem_text or len(problem_text) < 200:
                _say("agent", "LeetCode looked different today (maybe a login wall). "
                      "Falling back to my own notes on the statement.")
    except Exception as exc:
        _say("browser", f"couldn't open browser ({exc}). "
             "pip install playwright && python -m playwright install chromium")
        return False

    if not problem_text:
        problem_text = (f"{problem.title} — LeetCode {problem.difficulty}, "
                        f"pattern {problem.category}. I couldn't read the page.")
    _say("agent", "Reading problem...")
    und_reply, _ = brain.understand(problem_text)
    understanding = und_reply or "(brain silent)"
    _say("me", understanding[:400])

    # research
    resources_used = []
    notes_text = ""
    q = f"Explain the '{problem.concept}' pattern like I'm brand new, with a tiny C snippet if possible."
    for url in research.pages_for(problem):
        try:
            import urllib.request
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=12) as resp:
                html = resp.read().decode("utf-8", "ignore")
            title = page_title(html)
            body = research.readable_text(html)[:5500]
            _say("reading", f"{title} · {url}")
            summ_reply, _ = brain.read_resource(title, body, q)
            if summ_reply:
                _say("learned", summ_reply[:350])
                note_name = journal.record_note(problem.concept, title, url, summ_reply)
                notes_text += f"\n[{title}]: {summ_reply}"
                resources_used.append(url)
        except Exception as exc:
            _say("reading", f"{url} failed ({exc.__class__.__name__})")
            continue

    # plan
    plan_reply, _ = brain.plan(problem_text, understanding, notes_text)
    plan_text = plan_reply or "no plan came back; I'll wing it"
    _say("plan", textwrap.shorten(plan_text, 500, placeholder=" …"))

    # code
    code = None
    verdict = ""
    attempt = 0
    for attempt in range(3):
        fail_note = ("\nLast verdict/error: " + verdict) if verdict else ""
        code_reply, _ = brain.write_code(plan_text, problem_text, "", fail_note,
                                         prior_notes=notes_text)
        code = brain.extract_code(code_reply) or code_reply
        if not code or len(code.strip()) < 20:
            _say("me", "I can't write the code yet. Need to re-read the notes.")
            break

        # into the editor, run it
        try:
            with browser.Browser() as b:
                page = b.open_problem(problem.slug)
                b.ensure_c_language(page)
                b.set_code(page, code)
                ok = b.click_run(page)
                r_text = b.results_text(page, timeout=30) if ok else ""
        except Exception as exc:
            _say("browser", f"editor/lost control ({exc}). Pausing; judge manually.")
            r_text = ""

        results_sane = bool(r_text.strip())
        verdict_reply, _ = brain.verdict_interpret(r_text or "no readable result")
        passed = "accepted" in (r_text or "").lower() or (
            verdict_reply and ("accepted" in verdict_reply.lower()
                               or "passed" in verdict_reply.lower()))
        _say("run", textwrap.shorten(verdict_reply or
                                     (r_text[:300] if r_text else "couldn't read panel"),
                                     350, placeholder=" …"))
        tl = (r_text or "").lower()
        if "runtime error" in tl or "wrong answer" in tl or "compile error" in tl:
            passed = False
        if passed:
            verdict = "All visible tests passed under Run."
            break
        verdict = r_text[:400] or "no readable verdict"
        if attempt < 2:
            _say("me", "Not accepted on visible Run. Rethinking.")

    # when the agent *can't* submit: always let the human decide final submit
    print("\n  \033[93m─── [REVIEW] Code is in the editor. Please click SUBMIT "
          "yourself, ───\033[0m")
    print("      then come back and press <Enter> here (or 'n' to skip).")
    try:
        ack = input("\n   submitted? <Enter>=yes / n=skip: ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        ack = "n"
    submitted = (ack != "n")

    # journal (uses last attempt index even when loop ran 0×)
    ref_reply, _ = brain.reflect(problem_text,
                                 f"attempts: {attempt + 1}; last verdict: {verdict}",
                                 code or "")
    reflection = ref_reply or ("(offline: see plan and code above)")
    path = journal.record_problem(problem.slug, problem.title, problem.concept,
                                  provider, understanding, plan_text, code,
                                  "submitted" if submitted else "not-submitted",
                                  reflection, resources_used)
    concepts[problem.concept] = concepts.get(problem.concept, 0) + 1
    _say("journal", f"saved {path}")
    return True


def page_title(html):
    import re
    m = re.search(r"<title[^>]*>(.*?)</title>", html, re.S | re.I)
    if m:
        import html as _h
        return _h.unescape(m.group(1)).strip()[:120]
    return "untitled page"


def smoketest():
    """Import-level + plumbing check, no browser, no LLM: returns bool."""
    try:
        from . import curriculum, journal, research, browser as _b
        assert curriculum.next_problem([]) is not None
        assert curriculum.next_problem([p.slug for p in curriculum.NEETCODE_150]) is None
        assert research.pages_for(curriculum.NEETCODE_150[0])
        assert "journal" in journal.INDEX or not journal.entry_exists("two-sum")
        # Playwright import only (don't launch a window here)
        import playwright.sync_api  # noqa: F401
        return True
    except Exception as exc:
        print(f"smoketest failed: {exc}")
        return False
