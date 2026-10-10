"""Visible browser control for the learner agent.

Playwright, headed (a real window the user can watch), persistent profile
so the LeetCode session survives across runs. The agent types in the
editor and clicks RUN. It never clicks SUBMIT — the human does, by design.
"""

import os
import time

from playwright.sync_api import sync_playwright

LEETCODE = "https://leetcode.com"

_profile_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                            ".lc-profile")


class Browser:
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
            args=["--disable-blink-features=AutomationControlled"],
        )
        return self

    def __exit__(self, *exc):
        try:
            self.ctx.close()
        finally:
            self._pw.stop()
        return False

    # ── page helpers ────────────────────────────────────────────────────

    def new_page(self, url, wait=9):
        page = self.ctx.new_page()
        page.goto(url, wait_until="domcontentloaded", timeout=25_000)
        page.wait_for_timeout(wait * 1000)
        return page

    def open_problem(self, slug):
        return self.new_page(LEETCODE + f"/problems/{slug}/description/")

    # ── config (language = C, once) ─────────────────────────────────────

    def ensure_c_language(self, page):
        """Pick C in the language dropdown if it isn't already selected."""
        try:
            sel = page.locator("button:has-text('C++'), "
                               "div.select-wrapper button, "
                               "button[id^='headlessui']").first
            label = sel.inner_text(timeout=4000).strip()
            if label.startswith("C ") or label == "C":
                return
            sel.click()
            page.wait_for_timeout(800)
            page.locator("text='C'").first.click()
            page.wait_for_timeout(1200)
        except Exception:
            pass  # never hard-fail on cosmetics

    # ── read the problem ────────────────────────────────────────────────

    def problem_text(self, page):
        parts = []
        try:
            title = page.locator("a[href*='/problems/'] group above h3,"
                                 "h3").first.inner_text(timeout=5000)
        except Exception:
            title = ""
        try:
            body = page.locator(
                "div[id^='description'] div, div[data-track-load='description_content']"
            ).first.inner_text(timeout=6000)
        except Exception:
            try:
                body = page.locator("div.w-full:has(h3)").first.inner_text(timeout=4000)
            except Exception:
                body = ""
        parts = [t for t in (title, body) if t]
        return "\n".join(parts).strip()

    # ── editor interaction ──────────────────────────────────────────────

    def set_code(self, page, code):
        """Replace editor content: click into it, select-all, type."""
        clicked = False
        for sel in ("textarea", ".monaco-editor", ".view-lines",
                    "div[data-keybinding-context='1']"):
            try:
                page.locator(sel).first.click(timeout=4000)
                clicked = True
                break
            except Exception:
                continue
        if not clicked:
            page.mouse.click(700, 300)
        page.wait_for_timeout(400)
        page.keyboard.press("Control+A")
        page.wait_for_timeout(200)
        page.keyboard.type(code, delay=4)
        page.wait_for_timeout(500)

    def click_run(self, page):
        for sel in ("button:has-text('Run')", "button[data-layout='default']"):
            try:
                page.locator(sel).first.click(timeout=4000)
                return True
            except Exception:
                continue
        return False

    def results_text(self, page, timeout=40):
        """Poll the result console until something readable shows up."""
        deadline = time.time() + timeout
        while time.time() < deadline:
            try:
                for sel in ("div[data-layout='default']  pre.group",
                            "div.font-monospace",
                            "section.w-full pre",
                            "#result-panel"):
                    try:
                        txt = page.locator(sel).first.inner_text(timeout=2500)
                        if txt and len(txt.strip()) > 8:
                            return txt.strip()
                    except Exception:
                        continue
            except Exception:
                pass
            page.wait_for_timeout(2000)
        return ""

    def a11y_snapshot(self, page, limit=20000):
        try:
            data = page.accessibility.snapshot(interesting_only=True)
        except Exception:
            data = None
        import json
        return json.dumps(data, default=str)[:limit] if data else ""
