"""The /fcc solve loop: read task, ask the brain, paste it in, run tests,
submit. FCC mode is direct solving.

State lives in the same stress_state.json under state["fcc"]:
    {"done": {"js": [slugs], "html": [slugs]}, "stuck": {slug: reason}}

Session policy: when a challenge cannot be solved after 3 honest attempts,
the bot STOPS the whole session immediately - it does not plow into the
next challenge. Progress is saved before stopping so /fcc can resume.
"""

import json
import textwrap
import urllib.request

from . import brain, fcc_browser, fcc_curriculum


def _say(who, text, width=86):
    print(f"  \033[96m[{who}]\033[0m ", end="")
    print(textwrap.fill(str(text), width=width,
                        subsequent_indent=" " * (len(who) + 5)))


class Stuck(Exception):
    """Raised when a challenge is unsolvable - stops the session right away."""

    def __init__(self, slug, reason):
        self.slug = slug
        self.reason = reason
        super().__init__(f"stuck on {slug}: {reason}")


def load_progress(state):
    fcc = state.setdefault("fcc", {})
    done = fcc.setdefault("done", {})
    done.setdefault("js", [])
    done.setdefault("html", [])
    return fcc


def fetch_page_data(slug):
    """Fetch the challenge JSON (instructions, description, tests, starter).

    The same page-data the FCC site hydrates from - the authoritative source
    for what the tests demand, including conditions not shown in the panel.
    """
    url = fcc_curriculum.FCC + "/page-data" + slug + "/page-data.json"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=25) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    return data["result"]["data"]["challengeNode"]["challenge"]


def read_page(page_ctl, page, challenge):
    """Full task picture: FCC JSON + what the browser shows right now.

    For visual steps the description field tells the brain what the page
    renders; the editor's live content is read back so the brain knows
    exactly what sits in the editor before deciding what to change.
    """
    slug = challenge["slug"]
    title = challenge.get("title") or slug.rsplit("/", 1)[-1]

    try:
        cjson = fetch_page_data(slug)
    except Exception as exc:
        _say("net", f"page-data fetch failed ({exc}); falling back to screen text")
        cjson = {}

    instructions = cjson.get("instructions") or ""
    description = cjson.get("description") or ""
    tests = cjson.get("tests") or []

    if not (instructions or description):
        screen = page_ctl.challenge_task(page)
        instructions = screen or "(could not read the task)"

    starter = ""
    files = cjson.get("challengeFiles") or []
    if files:
        starter = files[0].get("contents") or ""
    try:
        live_editor = page_ctl.editor_content(page) or ""
    except Exception:
        live_editor = ""

    return {
        "title": title,
        "instructions": instructions,
        "description": description,
        "starter": starter,
        "tests": tests,
        "live_editor": live_editor,
    }


def build_prompt(task, lang, fail_note):
    """One self-contained prompt: exact task + tests + current editor state."""
    tests_text = "\n".join(
        "TEST: " + (t.get("text") or "") for t in task["tests"])
    editor_now = task["live_editor"] or task["starter"]
    return (
        f"Solve this freeCodeCamp {lang} challenge. Reply ONLY with the "
        f"complete code to put in the editor - no explanation, no markdown "
        f"fences.\n\nTitle: {task['title']}\n\n"
        f"Instructions:\n{task['instructions'][:2500]}\n\n"
        f"Page description (what the right panel renders right now):\n"
        f"{textwrap.shorten(task['description'], 2200) or '(none)'}\n\n"
        f"All tests that must pass (EVERY condition, exactly):\n"
        f"{tests_text[:2600]}\n\n"
        + (f"The HTML/JS editor currently contains EXACTLY this (modify it, "
           f"do not invent a new page):\n{editor_now[:1800]}\n\n"
           if editor_now else "")
        + (f"Your previous attempt FAILED with this test output:\n"
           f"{fail_note[:700]}\nFix it and return the FULL corrected file.\n\n"
           if fail_note else "")
        + "Remember: satisfy every test condition, including nesting rules "
          "like 'an a element should wrap around...', and keep all existing "
          "elements unless a test removes them."
    )


def solve_challenge(page_ctl, page, track, challenge, max_tries=3):
    """Work one challenge in the already-open page. True = submitted.

    Raises Stuck when it cannot be solved within max_tries - the session
    must stop immediately rather than skip ahead.
    """
    slug = challenge["slug"]
    lang = "html" if track == "html" else "javascript"
    task = read_page(page_ctl, page, challenge)
    tests_brief = "; ".join((t.get("text") or "") for t in task["tests"])[:150]
    _say("task", f"{task['title']} - [{lang}] - tests: {tests_brief}")

    fail_note = ""
    for attempt in range(1, max_tries + 1):
        reply, provider = brain.think_raw(build_prompt(task, lang, fail_note))
        code = brain.extract_code(reply) if reply else None
        if not code:
            code = reply  # maybe the model returned raw code without fences
        code = (code or "").strip()
        if len(code) < 5:
            raise Stuck(slug, "brain returned no usable code")

        _say("brain", f"solution received ({provider}) - typing it in "
                      f"(attempt {attempt}/{max_tries})")
        page_ctl.set_code(page, code)
        page.wait_for_timeout(800)

        if not page_ctl.click_run(page):
            _say("browser", "could not find the Run button")
            task["live_editor"] = page_ctl.editor_content(page) or ""
            continue
        passed, fail_text = page_ctl.tests_passed(page, timeout=45)
        _say("run", "ALL TESTS PASSED" if passed else
             textwrap.shorten(str(fail_text) or "tests did not pass", 200))
        if passed:
            # submit ONLY on a genuine pass - never after failures
            clicked = page_ctl.click_submit(page)
            _say("submit", "clicked Submit & moving on" if clicked else
                 "passed, but Submit button not visible (already advanced?)")
            return True

        fail_note = fail_text or "tests failed (no details captured)"
        task["live_editor"] = code  # editor now holds the failed attempt

    raise Stuck(slug, f"failed {max_tries} attempts; last error: "
                      f"{textwrap.shorten(str(fail_note), 220)}")


def run_session(state, n, tracks=("js", "html"), profile_dir=None):
    """Run a full FCC session; STOPS IMMEDIATELY when a step is unsolvable."""
    fcc = load_progress(state)
    done = fcc["done"]

    brain_reply, provider = brain.think(
        [{"role": "user", "content": "ping - 3 words max"}])
    if not brain_reply:
        print("\nNo brain: ollama is not running and no cloud key is set.")
        print("  Install:    winget install ollama")
        print("  Then:       ollama pull llama3")
        print("  Or set env: STRESS_CLOUD_BASE_URL + STRESS_CLOUD_API_KEY")
        return False

    for track in tracks:
        _say("fcc", f"=== {track.upper()} session -> {n} challenge(s) ===")
        with fcc_browser.FCCBrowser(profile_dir=profile_dir) as b:
            solved = 0
            try:
                while solved < n:
                    challenge = fcc_curriculum.next_unfinished(track, done[track])
                    if challenge is None:
                        _say("fcc", f"{track}: no unfinished solvable challenge found - "
                              "curriculum block exhausted or all marked done.")
                        break
                    _say("fcc", f"opening {challenge['slug']}")
                    page = b.open_challenge(challenge["slug"])

                    state_check = b.is_logged_in(page)
                    if state_check is False:
                        print("\n  Not signed in to freeCodeCamp.")
                        if not b.login_interactive():
                            _say("fcc", "still not logged in; stopping this track")
                            break
                        page = b.open_challenge(challenge["slug"])

                    try:
                        solve_challenge(b, page, track, challenge)
                    except Stuck as stuck:
                        fcc["stuck"] = {challenge["slug"]: stuck.reason}
                        state["fcc"] = fcc
                        print()
                        print(f"  STUCK on {challenge['slug']} - stopping right here.")
                        print(f"  Reason: {stuck.reason}")
                        print("  Nothing else will be attempted. Progress is saved;")
                        print("  fix the editor by hand (or upgrade the brain) and")
                        print("  run /fcc again to resume.")
                        return False
                    done[track].append(challenge["slug"])
                    fcc["done"] = done
                    state["fcc"] = fcc
                    solved += 1
                    _say("fcc", f"{solved}/{n} done this session")
            except KeyboardInterrupt:
                print()
                _say("fcc", "interrupted by you - progress saved, stopping.")
                return False
    return True


def run_session_infinite(state, n, tracks=("js", "html"), profile_dir=None):
    """Same as run_session but keeps going past stuck points (Ctrl+C to stop)."""
    fcc = load_progress(state)
    done = fcc["done"]
    try:
        for track in tracks:
            _say("fcc", f"=== {track.upper()} ENDLESS session ===")
            with fcc_browser.FCCBrowser(profile_dir=profile_dir) as b:
                while True:
                    challenge = fcc_curriculum.next_unfinished(track, done[track])
                    if challenge is None:
                        _say("fcc", f"{track}: nothing left in the curriculum")
                        break
                    _say("fcc", f"opening {challenge['slug']}")
                    page = b.open_challenge(challenge["slug"])
                    state_check = b.is_logged_in(page)
                    if state_check is False:
                        if not b.login_interactive():
                            _say("fcc", "still not logged in; stopping this track")
                            break
                        page = b.open_challenge(challenge["slug"])
                    try:
                        solve_challenge(b, page, track, challenge)
                    except Stuck as stuck:
                        fcc.setdefault("stuck", {})[challenge["slug"]] = stuck.reason
                        state["fcc"] = fcc
                        _say("fcc", f"stuck; skipping ahead: {stuck.reason}")
                    done[track].append(challenge["slug"])
                    fcc["done"] = done
                    state["fcc"] = fcc
    except KeyboardInterrupt:
        print()
        _say("fcc", "endless mode interrupted - progress saved.")


def smoketest():
    try:
        from . import fcc_browser, fcc_curriculum
        cur = fcc_curriculum.list_challenges("js")
        assert cur, "js curriculum empty"
        cur_h = fcc_curriculum.list_challenges("html")
        assert cur_h, "html curriculum empty"
        import playwright.sync_api
        return True
    except Exception as exc:
        print(f"fcc smoketest failed: {exc}")
        return False
