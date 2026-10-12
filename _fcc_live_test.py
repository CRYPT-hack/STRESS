"""Headless sanity run of the FCC solve loop against the real site.

Opens one challenge, logs in if needed, types the LLM's answer, clicks
Run the Tests, reports pass/fail, and clicks Submit only on success.
"""

import sys

sys.path.insert(0, ".")
from learner import fcc_browser, fcc_curriculum, fcc_driver  # noqa: E402


def main():
    track = "js"
    ch = fcc_curriculum.list_challenges(track)[0]
    print("challenge:", ch["slug"])
    with fcc_browser.FCCBrowser() as b:
        page = b.open_challenge(ch["slug"])
        li = b.is_logged_in(page)
        print("logged_in:", li)
        if li is False:
            ok = b.login_interactive()
            if not ok:
                print("RESULT: login never detected after 300 s")
                return 1
            page = b.open_challenge(ch["slug"])
        ok = fcc_driver.solve_challenge(b, page, track, ch)
        print("RESULT:", "submitted" if ok else "not submitted")
        return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
