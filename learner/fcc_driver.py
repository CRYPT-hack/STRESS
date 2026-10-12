"""The /fcc solve loop: read task, ask the brain, paste it in, run tests,
submit. No `beginner student` persona here — FCC mode is direct solving.

State lives in the same stress_state.json under state["fcc"]:
    {"done": {"js": [slugs], "html": [slugs]}}
"""

import json
import os
import textwrap

from . import brain, fcc_browser, fcc_curriculum


def _say(who, text, width=86):
    print(f"  \033[96m[{who}]\033[0m ", end="")
    print(textwrap.fill(str(text), width=width,
                        subsequent_indent=" " * (len(who) + 5)))


def load_progress(state):
    fcc = state.setdefault("fcc", {})
    done = fcc.setdefault("done", {})
    done.setdefault("js", [])
    done.setdefault("html", [])
    return fcc


def solve_challenge(page_ctl, page, track, challenge, provider_hint=None,
                    max_tries=3):
    """Work one challenge in the already-open page. Returns True on submit."""
    slug = challenge["slug"]
    title = challenge.get("title") or slug.rsplit("/", 1)[-1]

    # fetch the challenge JSON (instructions, starter code, tests) — the
    # same page-data the site itself hydrates from
    task = fcc_curriculum and ""
    try:
        import urllib.request
        url = fcc_curriculum.FCC + "/page-data" + slug + "/page-data.json"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=25) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        cjson = data["result"]["data"]["challengeNode"]["challenge"]
    except Exception as exc:
        _say("net", f"page-data fetch failed ({exc}); falling back to screen text")
        cjson = {}

    instructions = cjson.get("instructions") or ""
    description = cjson.get("description") or ""
    starter = ""
    files = cjson.get("challengeFiles") or []
    if files:
        starter = files[0].get("contents") or ""
    tests_text = "\n".join("TEST: " + (t.get("text") or "") for t in (cjson.get("tests") or []))
    # If page hydration failed, at least give the brain the on-screen text
    lang = "html" if track == "html" else "javascript"
    if not (instructions or description):
        screen = page_ctl.challenge_task(page)
        description = screen or "(could not read the task)"

    _say("task", f"{title} · [{lang}] · tests: {(tests_text or '')[:150]}")

    # ── ask the brain for a direct solution ────────────────────────────
    fail_note = ""
    for attempt in range(1, max_tries + 1):
        prompt = (
            f"Solve this freeCodeCamp {lang} challenge. Reply ONLY with the "
            f"complete code to put in the editor — no explanation, no markdown "
            f"fences.\n\nTitle: {title}\n\n"
            f"Instructions:\n{instructions[:2500]}\n\n"
            f"Description (HTML):\n{textwrap.shorten(description, 2200)}\n\n"
            f"All tests that must pass (EVERY one; satisfy each condition "
            f"exactly):\n{tests_text[:2200]}\n\n"
            + (f"Starter code to build on:\n{starter[:1200]}\n\n" if starter else "")
            + (f"Your previous attempt FAILED with: {fail_note[:600]}\n"
               "Fix it and return the full corrected code.\n\n" if fail_note else "")
        )
        reply, provider = brain.think_raw(prompt)
        code = brain.extract_code(reply) if reply else None
        if not code:
            code = reply  # maybe the model returned raw code without fences
        code = (code or "").strip()
        if len(code) < 5:
            _say("brain", "no usable code came back; skipping challenge")
            return False
        _say("brain", f"solution received ({provider}) — typing it in "
                      f"(attempt {attempt}/{max_tries})")

        page_ctl.set_code(page, code)
        page.wait_for_timeout(800)

        if not page_ctl.click_run(page):
            _say("browser", "couldn't find the Run button")
            continue
        passed, fail_text = page_ctl.tests_passed(page, timeout=45)
        _say("run", "ALL TESTS PASSED ✓" if passed else
             textwrap.shorten(fail_text or "tests didn't pass", 200, placeholder=" …"))
        if passed:
            # submit ONLY on a genuine pass — never after failures
            clicked = page_ctl.click_submit(page)
            _say("submit", "clicked 'Submit' & moving on ✓" if clicked else
                 "passed, but Submit button not visible (already advanced?)")
            return True
        fail_note = fail_text or "tests failed (no details captured)"

    _say("fcc", "3 attempts failed — NOT submitting. Marked to retry next session.")
    return False


def run_session(state, N, tracks=("js", "html"), profile_dir=None):
    """Run a full FCC session.

    tracks: tuple like ("js",) or ("js", "html") — html and js each get
    their own browser window (separate Chromium contexts on one launcher).
    """
    fcc = load_progress(state)
    done = fcc["done"]

    brain_reply, provider = brain.think(
        [{"role": "user", "content": "ping — 3 words max"}])
    if not brain_reply:
        print("\nNo brain: ollama isn't running and no cloud key is set.")
        print("  Install:    winget install ollama")
        print("  Then:       ollama pull llama3")
        print("  Or set env: STRESS_CLOUD_BASE_URL + STRESS_CLOUD_API_KEY")
        return False

    # separate profile per track so both sessions stay signed in and don't
    # fight over the same Chromium user-data-dir
    per_track = 1 if len(tracks) == 1 else (N + 1) // 2

    for track in tracks:
        n_here = N if len(tracks) == 1 else per_track
        _say("fcc", f"=== {track.upper()} session → {n_here} challenge(s) ===")
        with fcc_browser.FCCBrowser(profile_dir=profile_dir) as b:
            page = None
            solved = 0
            while solved < n_here:
                challenge = fcc_curriculum.next_unfinished(track, done[track])
                if challenge is None:
                    _say("fcc", f"{track}: no unfinished solvable challenge found — "
                          "curriculum block exhausted or all marked done.")
                    break
                _say("fcc", f"opening {challenge['slug']}")
                page = b.open_challenge(challenge["slug"])

                state_check = b.is_logged_in(page)
                if state_check is False:
                    print("\n  \033[93mNot signed in to freeCodeCamp.\033[0m")
                    if not b.login_interactive():
                        _say("fcc", "still not logged in; stopping this track")
                        break
                    page = b.open_challenge(challenge["slug"])

                ok = solve_challenge(b, page, track, challenge)
                if ok:
                    done[track].append(challenge["slug"])
                    fcc["done"] = done
                    state["fcc"] = fcc
                    solved += 1
                else:
                    fcc.setdefault("skipped", []).append(challenge["slug"])
                    state["fcc"] = fcc
                    _say("fcc", "marked to retry next session")
    return True


def smoketest():
    try:
        from . import fcc_browser, fcc_curriculum  # noqa: F401
        cur = fcc_curriculum.list_challenges("js")
        assert cur, "js curriculum empty"
        cur_h = fcc_curriculum.list_challenges("html")
        assert cur_h, "html curriculum empty"
        import playwright.sync_api  # noqa: F401
        return True
    except Exception as exc:
        print(f"fcc smoketest failed: {exc}")
        return False
