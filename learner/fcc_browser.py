"""Visible browser control for the freeCodeCamp learner.

Playwright, headed, persistent profile (`.fcc-profile`) so the FCC login
survives across runs. Unlike the LeetCode adapter, the FCC bot is fully
automatic: it types into the editor, clicks "Run the Tests", and — when
all tests pass — clicks Submit itself.

Buttons are located by role/text at run time (FCC re-skins often), not
by brittle data-cy attributes.
"""

import json
import os
import time

from playwright.sync_api import sync_playwright

FCC = "https://www.freecodecamp.org"

_profile_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                            ".fcc-profile")


class FCCBrowser:
    """Owns the Playwright lifecycle; use as a context manager."""

    def __init__(self, headless=False, profile_dir=None):
        self.headless = headless
        self.profile_dir = profile_dir or _profile_dir
        self._pw = None
        self.ctx = None

    def __enter__(self):
        self._pw = sync_playwright().start()
        self.ctx = self._pw.chromium.launch_persistent_context(
            user_data_dir=self.profile_dir,
            headless=self.headless,
            viewport={"width": 1380, "height": 900},
        )
        return self

    def __exit__(self, *exc):
        try:
            self.ctx.close()
        finally:
            self._pw.stop()
        return False

    # ── navigation ──────────────────────────────────────────────────────

    def open(self, url, wait=6):
        page = self.ctx.new_page()
        page.goto(url, wait_until="domcontentloaded", timeout=40_000)
        page.wait_for_timeout(wait * 1000)
        return page

    def open_challenge(self, slug):
        return self.open(FCC + slug, wait=7)

    # ── login state ─────────────────────────────────────────────────────

    def is_logged_in(self, page):
        """Heuristic: FCC shows the top nav avatar/profile link once signed in."""
        for sel in ("img[alt*='avatar']", "img[alt*='Avatar']",
                    "button[aria-label*='menu']", "a[href*='/settings']"):
            try:
                if page.locator(sel).first.is_visible(timeout=2500):
                    return True
            except Exception:
                continue
        try:
            if page.locator("a:has-text('Sign in')").first.is_visible(timeout=1500):
                return False
        except Exception:
            pass
        return None  # unknown

    def login_interactive(self, url=FCC):
        """Open the site and wait (max 5 min) for the human to sign in."""
        page = self.open(url, wait=3)
        print("  \033[93m─── Sign in inside the opened browser window. ───\033[0m")
        print("  (The bot waits up to 5 minutes, then re-checks.)")
        deadline = time.time() + 300
        while time.time() < deadline:
            state = self.is_logged_in(page)
            if state is True:
                print("  \033[92mLogged in ✓\033[0m — saving session to .fcc-profile")
                return True
            page.wait_for_timeout(3000)
        return False

    # ── challenge reading ───────────────────────────────────────────────

    def challenge_task(self, page):
        """Pull instructions + description text from the left panel."""
        parts = []
        for sel in ("#description, [id^='description'] p, div[role='region'] p"):
            try:
                txt = page.locator(sel).all_inner_texts(timeout=4000)
                if txt:
                    parts.extend(t for t in txt if t.strip())
                    break
            except Exception:
                continue
        return "\n".join(parts).strip()

    def editor_content(self, page):
        """Read current editor content via Monaco's textarea mirror."""
        try:
            ta = page.locator("textarea").first
            return ta.input_value(timeout=4000)
        except Exception:
            return ""

    # ── editor interaction ──────────────────────────────────────────────

    def set_code(self, page, code, first_only=False):
        """Click into the editor, select-all, replace the content."""
        clicked = False
        for sel in (".monaco-editor textarea", ".monaco-editor", ".view-lines"):
            try:
                page.locator(sel).first.click(timeout=6000)
                clicked = True
                break
            except Exception:
                continue
        if not clicked:
            page.mouse.click(900, 450)      # editor pane on a 1380×900 view
            page.wait_for_timeout(400)
        page.keyboard.press("Control+A")
        page.wait_for_timeout(250)
        page.keyboard.type(code, delay=2)
        page.wait_for_timeout(400)

    # ── run + submit ────────────────────────────────────────────────────

    def click_run(self, page):
        """The current FCC button is labeled 'Check Your Code' (data-cy omitted
        in places); older builds say 'Run the Tests'.
        """
        for sel in ("button:has-text('Check Your Code')",
                    "button:has-text('Run the Tests')",
                    "button:has-text('Run')", "[data-cy='run-tests-button']",
                    ".btn-cta"):
            try:
                page.locator(sel).first.click(timeout=5000)
                return True
            except Exception:
                continue
        # fall back: first enabled button with a cta class + play icon
        try:
            page.locator("button.btn-cta").first.click(timeout=4000)
            return True
        except Exception:
            return False

    def click_submit(self, page):
        """After success the panel shows 'Submit and go to next challenge' 
        (older builds just 'Submit').
        """
        for sel in ("button:has-text('Submit and go to next challenge')",
                    "button:has-text('go to next challenge')",
                    "button:has-text('Submit')", "[data-cy='submit-button']"):
            try:
                btn = page.locator(sel).first
                if btn.is_visible(timeout=2500):
                    btn.click(timeout=4000)
                    page.wait_for_timeout(2500)
                    return True
            except Exception:
                continue
        return False

    def tests_passed(self, page, timeout=45):
        """Poll FCC's per-test result blocks.

        FCC renders one `.test-result` element per test; success means ALL
        of them start with 'Passed:' (and a Submit button becomes visible).
        There is NO 'all tests passed' banner on this build.
        """
        import time as _time
        deadline = _time.time() + timeout
        fail_text = ""
        while _time.time() < deadline:
            try:
                n = page.locator(".test-result").count()
                if n:
                    results = [page.locator(".test-result").nth(i)
                               .inner_text(timeout=1500).strip()
                               for i in range(n)]
                    if all(r.startswith("Passed") for r in results):
                        return True, ""
                    failed = [r for r in results if r.startswith("Failed")]
                    if failed:
                        fail_text = "\n".join(failed)[:800]
            except Exception:
                pass
            # success shortcut: FCC shows the Submit button only on pass
            try:
                if page.locator("button:has-text('Submit')").first.is_visible(
                        timeout=1200):
                    return True, ""
            except Exception:
                pass
            page.wait_for_timeout(2000)
        return False, fail_text or "timed out waiting for tests to pass"

    # ── misc ────────────────────────────────────────────────────────────

    def current_url(self, page):
        return page.url

    def dump_dom(self, page, limit=4000):
        return page.content()[:limit]
