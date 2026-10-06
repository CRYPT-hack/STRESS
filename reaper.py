#!/usr/bin/env python3
"""GRIM — the STRESS desktop reaper.

A little grim reaper who lives on your screen, roams around on his own,
and periodically stops you with speech-bubble questions from the STRESS
bank (ML, DSA, Linear Algebra). Answers count toward the same daily
quota, streak and redemption ledger as the terminal bot — same state
file, same rules. He also talks, if speech-dispatcher is available.

Run:  python3 reaper.py [--size 190] [--min-gap 4] [--max-gap 9]
                      [--no-voice] [--test]

Left-click: taunt   ·   double-click: quiz now   ·   right-click: menu
The window is click-through everywhere except the reaper and his bubble.
"""

import argparse
import math
import os
import random
import shutil
import subprocess
import sys

if os.environ.get("DISPLAY"):
    # XWayland is the only backend where the reaper can position himself
    # freely; override whatever the session preset (usually "wayland").
    os.environ["GDK_BACKEND"] = "x11"
else:
    os.environ.pop("GDK_BACKEND", None)  # bare Wayland fallback: no roaming

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import gi  # noqa: E402
gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
gi.require_version("GdkPixbuf", "2.0")
from gi.repository import Gdk, GdkPixbuf, GLib, Gtk  # noqa: E402

import grader  # noqa: E402
import quiz as quizsel  # noqa: E402
import state as st  # noqa: E402
from questions import BANK, SUBJECT_NAMES, SUBJECTS  # noqa: E402
from enforcer import FAREWELL, MOTIVATION, PRAISE, WRONG, line  # noqa: E402

TICK_MS = 33
QUIZ_TIMEOUT_S = 90
FEEDBACK_S = 7
QUIP_S = 6
MAX_BUBBLE_W = 360
DEBUG = os.environ.get("STRESS_GRIM_DEBUG") == "1"

TAUNTS = [
    "I can see you tabbed away. I have a scythe and infinite patience.",
    "Netflix will still be there after your quota. I won't.",
    "Every scroll is a rep you owe me.",
    "Dead men don't need DSA. You're not dead yet. Back to work.",
    "I harvested 9,412 souls who skipped linear algebra. Don't be 9,413.",
    "You've been idle for a suspiciously long time...",
    "The streak lives as long as you do. Keep it that way.",
]

ASK_LINES = [
    "Answer, mortal.",
    "The reaper demands an answer.",
    "Pop quiz. Scream later.",
    "Your quota knocked. I let it in.",
]

QUIP_LEAD = ["Psst.", "Hey.", "Listen.", "Mortal.", "A word."]

CSS = b"""
.pet-root { background-color: rgba(0,0,0,0); }
.bubble {
    background-color: rgba(10,9,14,0.97);
    background-image: linear-gradient(to bottom,
        rgba(34,20,30,0.97), rgba(9,8,13,0.97));
    border: 1px solid rgba(255,82,82,0.65);
    border-radius: 14px;
    padding: 12px 14px 12px 14px;
}
.qhead { color: #ffb4b4; font-weight: bold; font-size: 11px; padding-bottom: 5px; }
.qtext {
    color: #ffffff; font-size: 13px; font-weight: 600;
    text-shadow: 0 1px 2px rgba(0,0,0,0.9);
}
.quip {
    color: #ffe9c4; font-size: 13px; font-style: italic;
    text-shadow: 0 0 4px rgba(255,180,80,0.35);
}
.fb-good {
    color: #3ddc84; font-size: 13px; font-weight: bold;
    text-shadow: 0 0 5px rgba(61,220,132,0.45);
}
.fb-bad {
    color: #ff5566; font-size: 13px; font-weight: bold;
    text-shadow: 0 0 5px rgba(255,85,102,0.45);
}
.fb-note { color: #c9c9d4; font-size: 11.5px; font-style: italic; }
.bubble button {
    background-color: rgba(52,20,26,0.97);
    background-image: linear-gradient(to bottom,
        rgba(88,28,36,0.97), rgba(46,17,22,0.97));
    color: #ffecec; font-size: 12px; font-weight: 600;
    border: 1px solid rgba(255,96,96,0.5);
    border-radius: 9px; padding: 5px 10px;
}
.bubble button:hover {
    background-image: linear-gradient(to bottom,
        rgba(160,38,50,0.98), rgba(104,24,32,0.98));
    color: #ffffff;
    border-color: rgba(255,130,130,0.9);
}
.bubble entry {
    background: rgba(24,20,28,0.97); color: #ffffff; font-size: 12px;
    caret-color: #ff5566;
    border: 1px solid rgba(255,96,96,0.5); border-radius: 9px; padding: 5px 9px;
}
.bubble entry:focus { border-color: rgba(255,130,130,0.95); }
"""


def markup_escape(text):
    return GLib.markup_escape_text(str(text), -1)


class Reaper(Gtk.Window):
    def __init__(self, cfg):
        super().__init__(title="STRESS reaper")
        self.cfg = cfg
        self.state = st.load()
        if self.state["name"] is None:
            self.state["name"] = "recruit"
            st.save(self.state)
        died, missed, old = st.ensure_today(self.state)
        st.save(self.state)

        self.voice_on = cfg.voice and shutil.which("spd-say") is not None
        if cfg.voice and self.voice_on is False:
            print("note: spd-say not found, running silent "
                  "(speech-dispatcher provides the voice)")

        screen = Gdk.Screen.get_default()
        root_w = screen.get_root_window().get_geometry()
        self.screen_w, self.screen_h = root_w[2], root_w[3]
        visual = screen.get_rgba_visual()
        if visual is not None:
            self.set_visual(visual)

        self.set_decorated(False)
        self.set_keep_above(True)
        self.set_skip_taskbar_hint(True)
        self.set_skip_pager_hint(True)
        self.set_accept_focus(False)
        self.set_focus_on_map(False)
        self.set_resizable(False)
        self.set_app_paintable(True)
        self.get_style_context().add_class("pet-root")

        provider = Gtk.CssProvider()
        provider.load_from_data(CSS)
        Gtk.StyleContext.add_provider_for_screen(
            screen, provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

        self.pix_right, self.pix_left, self.sw, self.sh = self._load_sprites()
        self.img = Gtk.Image.new_from_pixbuf(self.pix_right)
        self.bubble = Gtk.EventBox()
        self.bubble.get_style_context().add_class("bubble")
        self.bubble_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.bubble.add(self.bubble_box)

        self.fixed = Gtk.Fixed()
        self.fixed.put(self.bubble, 0, 0)
        self.fixed.put(self.img, 0, 0)
        self.add(self.fixed)

        self.bubble_visible = False
        self.current_q = None
        self.quiz_timer_id = None
        self.bubble_timer_id = None
        self.voice_proc = None

        self.sx = random.uniform(80, max(81, self.screen_w - self.sw - 80))
        self.sy = random.uniform(260, max(261, self.screen_h - self.sh - 60))
        self.tx, self.ty = self.sx, self.sy
        self.facing_left = False
        self.moving = False
        self.phase = random.uniform(0, 6)
        self.frozen = False

        self.connect("destroy", Gtk.main_quit)
        self.connect("button-press-event", self.on_click)
        self.add_events(Gdk.EventMask.BUTTON_PRESS_MASK)

        self.resize(self.sw, self.sh)
        self.move(round(self.sx), round(self.sy))
        self._W, self._H = self.sw, self.sh
        self.realize()
        self._shape_input()
        self.show_all()
        self.bubble.hide()

        GLib.timeout_add(TICK_MS, self._tick)
        GLib.timeout_add(int(random.uniform(600, 2000)), self._wake)
        first = 8 if cfg.test else random.uniform(25, 60)
        GLib.timeout_add_seconds(int(first), self._scheduled_quiz)
        GLib.timeout_add_seconds(
            int(45 if cfg.test else random.uniform(120, 240)), self._idle_quip)

        if died:
            GLib.timeout_add_seconds(
                2, lambda: (self.say_bubble(
                    line(streak_lines, missed=missed, streak=old), None, 6), False)[1])

    # ── sprites & input shape ────────────────────────────────────────────

    def _load_sprites(self):
        path_r = os.path.join(HERE, "assets", "reaper.png")
        path_l = os.path.join(HERE, "assets", "reaper_flip.png")
        for p in (path_r, path_l):
            if not os.path.exists(p):
                raise SystemExit(f"missing {p}; run: python3 make_sprites.py")
        pr = GdkPixbuf.Pixbuf.new_from_file(path_r)
        pl = GdkPixbuf.Pixbuf.new_from_file(path_l)
        h = self.cfg.size
        w = round(pr.get_width() * h / pr.get_height())
        pr = pr.scale_simple(w, h, GdkPixbuf.InterpType.BILINEAR)
        pl = pl.scale_simple(w, h, GdkPixbuf.InterpType.BILINEAR)
        return pr, pl, w, h

    def _shape_input(self):
        """Click-through everywhere but the reaper (and bubble, when up).

        Uses an X11 1-bit input mask (LSB-first bytes, rows padded to
        bytes) — avoids the pycairo/GObject region bridge entirely.
        """
        gdk_win = self.get_window()
        if gdk_win is None:
            return
        W, H = self._W, self._H
        bpr = (W + 7) // 8
        mask = bytearray(bpr * H)

        def fill_rect(x0, y0, w, h):
            for y in range(max(0, y0), min(H, y0 + h)):
                base = y * bpr
                for x in range(max(0, x0), min(W, x0 + w)):
                    mask[base + x // 8] |= 1 << (x & 7)

        sw, sh = self.sw, self.sh
        ox = (W - sw) // 2 if self.bubble_visible else 0
        oy = self._bubble_height() if self.bubble_visible else 0
        stride = self.pix_right.get_rowstride()
        nch = self.pix_right.get_n_channels()
        buf = self.pix_right.get_pixels()
        for y in range(sh):
            base = (oy + y) * bpr
            srow = y * stride
            for x in range(sw):
                if buf[srow + x * nch + (nch - 1)] > 40:
                    mask[base + (ox + x) // 8] |= 1 << ((ox + x) & 7)
        if self.bubble_visible:
            fill_rect((W - self._bubble_width()) // 2, 0,
                      self._bubble_width(), min(self._bubble_height() + 8, H))
        try:
            bmp = Gdk.bitmap_create_from_data(gdk_win, bytes(mask), W, H)
            gdk_win.input_shape_combine_mask(bmp, 0, 0)
        except Exception:
            pass  # no X11 shaping: whole window stays clickable, still fine

    # ── bubble geometry ──────────────────────────────────────────────────

    def _bubble_width(self):
        return min(MAX_BUBBLE_W, max(self.sw, 280))

    def _bubble_height(self):
        if not self.bubble_visible:
            return 0
        w = self._bubble_width()
        _, nat = self.bubble.get_preferred_height_for_width(w)
        return nat

    def _layout(self):
        if self.bubble_visible:
            bw, bh = self._bubble_width(), max(self._bubble_height(), 40)
            W = max(bw, self.sw) + 8
            H = bh + self.sh
            self._W, self._H = W, H
            self.fixed.move(self.bubble, (W - bw) // 2, 0)
            self.fixed.move(self.img, (W - self.sw) // 2, bh)
            self.resize(W, H)
            if self.sy - bh < 2:
                self.sy = min(bh + 2, self.screen_h - self.sh - 2)
            self.move(round(self.sx - (W - self.sw) // 2), round(self.sy - bh))
        else:
            self._W, self._H = self.sw, self.sh
            self.fixed.move(self.img, 0, 0)
            self.resize(self.sw, self.sh)
            self.move(round(self.sx), round(self.sy))
        self._shape_input()

    # ── roaming ──────────────────────────────────────────────────────────

    def _pick_target(self):
        margin_x = 20
        self.tx = random.uniform(margin_x, self.screen_w - self.sw - margin_x)
        self.ty = random.uniform(250, self.screen_h - self.sh - 50)
        self.speed = random.uniform(55, 110) * (self.cfg.size / 190) * self.cfg.speed

    def _tick(self):
        if not self.frozen:
            self.phase += 0.11
            dx, dy = self.tx - self.sx, self.ty - self.sy
            dist = math.hypot(dx, dy)
            if dist < 4:
                if self.moving:
                    self.moving = False
                    GLib.timeout_add(
                        int(random.uniform(1200, 5000)), self._wake)
            else:
                step = min(self.speed * TICK_MS / 1000, dist)
                self.sx += dx / dist * step
                self.sy += dy / dist * step
                self.moving = True
                want_left = dx < -1
                if want_left != self.facing_left:
                    self.facing_left = want_left
                    self.img.set_from_pixbuf(
                        self.pix_left if want_left else self.pix_right)
            bob = round(math.sin(self.phase) * 3) if self.moving else \
                round(math.sin(self.phase * 0.5) * 1)
            self.move(round(self.sx), round(self.sy) + bob)
            if DEBUG:
                n = getattr(self, "_dbg_n", 0) + 1
                self._dbg_n = n
                if n % 30 == 0:
                    geo = self.get_window().get_geometry()
                    print(f"dbg: logical=({round(self.sx)},{round(self.sy)}) "
                          f"gdk=({geo[0]},{geo[1]}) moving={self.moving}",
                          flush=True)
        return True

    def _wake(self, *a):
        self._pick_target()
        return False

    # ── speech ───────────────────────────────────────────────────────────

    def speak(self, text):
        if not self.voice_on:
            return
        if self.voice_proc is not None:
            try:
                self.voice_proc.terminate()
            except OSError:
                pass
        text = " ".join(text.replace("💀", "").split())[:400]
        try:
            self.voice_proc = subprocess.Popen(
                ["spd-say", "-p", "-60", "-r", "-15", text],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except OSError:
            pass

    def _clear_bubble_timer(self):
        if self.bubble_timer_id is not None:
            GLib.source_remove(self.bubble_timer_id)
            self.bubble_timer_id = None

    def say_bubble(self, text, note=None, seconds=QUIP_S):
        """Plain speech bubble, no interaction."""
        self._clear_bubble_timer()
        for c in self.bubble_box.get_children():
            self.bubble_box.remove(c)
        head = Gtk.Label()
        head.set_markup(f'💀 <span font_size="110%">{markup_escape(text)}</span>')
        head.set_line_wrap(True)
        head.get_style_context().add_class("quip")
        head.set_size_request(self._bubble_width() - 24, -1)
        self.bubble_box.pack_start(head, False, False, 0)
        if note:
            n = Gtk.Label(label=note)
            n.get_style_context().add_class("fb-note")
            n.set_line_wrap(True)
            n.set_size_request(self._bubble_width() - 24, -1)
            self.bubble_box.pack_start(n, False, False, 0)
        self._show_bubble()
        self.bubble_timer_id = GLib.timeout_add_seconds(
            seconds, lambda: (self._hide_bubble(), False)[1])
        self.speak(text)

    def ask_question(self):
        if self.frozen:
            return
        subj = random.choice(SUBJECTS)
        q, recycled = quizsel.pick_question(
            BANK, set(st.bucket(self.state)["asked_ids"]), subject=subj)
        self.current_q = q
        self.frozen = True
        self._clear_bubble_timer()
        for c in self.bubble_box.get_children():
            self.bubble_box.remove(c)

        head = Gtk.Label()
        head.set_markup(
            f'<span background="#9b1c1c" foreground="#ffffff" weight="bold"> '
            f'{markup_escape(SUBJECT_NAMES[q.subject])} </span>'
            f'  <span foreground="#ffd166">{"●" * q.difficulty}'
            f'{"○" * (3 - q.difficulty)}</span>'
            f'   <span foreground="#ff9db1" style="italic">'
            f'{markup_escape(random.choice(ASK_LINES))}</span>')
        head.get_style_context().add_class("qhead")
        head.set_size_request(self._bubble_width() - 24, -1)
        self.bubble_box.pack_start(head, False, False, 0)

        body = Gtk.Label()
        body.set_markup(markup_escape(q.q))
        body.get_style_context().add_class("qtext")
        body.set_line_wrap(True)
        body.set_size_request(self._bubble_width() - 24, -1)
        self.bubble_box.pack_start(body, False, False, 0)

        if q.options:
            for i, opt in enumerate(q.options):
                btn = Gtk.Button(label=f"{chr(65 + i)})  {opt}")
                btn.connect("clicked", self._on_choice, i)
                self.bubble_box.pack_start(btn, False, False, 0)
        else:
            self.entry = Gtk.Entry()
            self.entry.set_placeholder_text("type your answer, then Enter")
            self.entry.connect("activate", self._on_entry)
            self.bubble_box.pack_start(self.entry, False, False, 0)
            row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
            ok = Gtk.Button(label="Answer")
            ok.connect("clicked", self._on_entry)
            reveal = Gtk.Button(label="Surrender")
            reveal.connect("clicked", lambda b: self._finish_question(False, reveal=True))
            row.pack_start(ok, False, False, 0)
            row.pack_start(reveal, False, False, 0)
            self.bubble_box.pack_start(row, False, False, 0)

        self._show_bubble()
        if DEBUG:
            print(f"dbg: quiz shown window={self._W}x{self._H} "
                  f"bubble_h={self._bubble_height()} options={bool(q.options)}",
                  flush=True)
        if not q.options:
            self.get_window().set_accept_focus(True)
            self.entry.grab_focus()
        self.speak(q.q)
        self.bubble_timer_id = GLib.timeout_add_seconds(
            QUIZ_TIMEOUT_S,
            lambda: (self._finish_question(False, timeout=True), False)[1])

    def _show_bubble(self):
        self.bubble_visible = True
        self.bubble.show_all()
        self._layout()

    def _hide_bubble(self):
        self._clear_bubble_timer()
        self.bubble_visible = False
        self.bubble.hide()
        try:
            self.get_window().set_accept_focus(False)
        except AttributeError:
            pass
        self._layout()
        return False

    # ── grading ──────────────────────────────────────────────────────────

    def _on_choice(self, btn, i):
        self._finish_question(i == self.current_q.answer)

    def _on_entry(self, *a):
        if self.current_q is None:
            return
        reply = self.entry.get_text()
        self._finish_question(grader.grade(self.current_q, reply))

    def _finish_question(self, correct, reveal=False, timeout=False):
        if self.current_q is None:
            return False
        q, self.current_q = self.current_q, None
        was_met = st.quota_met(self.state)
        st.record_attempt(self.state, q.subject, correct, q.qid)
        if correct:
            st.clear_failed(self.state, q.qid)
        else:
            st.mark_failed(self.state, q.qid)
        st.save(self.state)

        self._clear_bubble_timer()
        for c in self.bubble_box.get_children():
            self.bubble_box.remove(c)
        try:
            self.get_window().set_accept_focus(False)
        except AttributeError:
            pass

        answer_text = q.options[q.answer] if q.options else " / ".join(q.open_answers)
        if correct:
            msg = Gtk.Label()
            msg.set_markup(
                f'✔ <span size="110%">{markup_escape(line(PRAISE))}</span>')
            msg.get_style_context().add_class("fb-good")
            self.bubble_box.pack_start(msg, False, False, 0)
            if q.explanation:
                note = Gtk.Label(label=q.explanation)
                note.get_style_context().add_class("fb-note")
                note.set_line_wrap(True)
                note.set_size_request(self._bubble_width() - 24, -1)
                self.bubble_box.pack_start(note, False, False, 0)
            self.speak("Correct.")
        else:
            why = "time's up — the scythe waited in vain" if timeout else \
                  ("surrendered" if reveal else "wrong")
            msg = Gtk.Label()
            msg.set_markup(
                f'✘ {why}! Answer: '
                f'<span foreground="#ffd166" weight="bold">'
                f'{markup_escape(answer_text)}</span>')
            msg.get_style_context().add_class("fb-bad")
            self.bubble_box.pack_start(msg, False, False, 0)
            if q.explanation:
                note = Gtk.Label(label=q.explanation)
                note.get_style_context().add_class("fb-note")
                note.set_line_wrap(True)
                note.set_size_request(self._bubble_width() - 24, -1)
                self.bubble_box.pack_start(note, False, False, 0)
            self.speak(f"Wrong. The answer was {answer_text}.")

        if not was_met and st.quota_met(self.state):
            new = st.complete_quota(self.state)
            st.save(self.state)
            done = Gtk.Label()
            done.set_markup(
                f'<span size="115%" weight="bold">💀 DAILY QUOTA COMPLETE'
                f'</span> — <span foreground="#ffd166">streak {new}🔥</span>')
            done.get_style_context().add_class("fb-good")
            self.bubble_box.pack_start(done, False, False, 0)
            self.speak(line(FAREWELL))

        self._show_bubble()
        self.bubble_timer_id = GLib.timeout_add_seconds(
            FEEDBACK_S, lambda: (self._end_quiz(), False)[1])
        return False

    def _end_quiz(self):
        self._hide_bubble()
        self.frozen = False
        self.current_q = None
        self._pick_target()
        gap = random.uniform(self.cfg.min_gap, self.cfg.max_gap)
        if self.cfg.test:
            gap = random.uniform(25, 45)
        GLib.timeout_add_seconds(int(gap), self._scheduled_quiz)
        return False

    # ── scheduled events ─────────────────────────────────────────────────

    def _scheduled_quiz(self, *a):
        if self.frozen:  # mid-quiz (manual double-click); try again shortly
            GLib.timeout_add_seconds(60, self._scheduled_quiz)
            return False
        self.ask_question()
        return False

    def _idle_quip(self, *a):
        if not self.frozen:
            met = st.quota_met(self.state)
            if met:
                pool = ["Quota met. I'm just here for the vibes and souls.",
                        line(FAREWELL)] + MOTIVATION[:2]
            else:
                pool = TAUNTS + [line(MOTIVATION)]
            self.say_bubble(f"{random.choice(QUIP_LEAD)} {random.choice(pool)}",
                            seconds=QUIP_S)
        GLib.timeout_add_seconds(
            int(60 if self.cfg.test else random.uniform(150, 320)), self._idle_quip)
        return False

    # ── interaction ──────────────────────────────────────────────────────

    def on_click(self, w, event):
        if event.button == 3:
            self._popup_menu(event)
            return True
        if self.frozen:
            return True
        if event.type == Gdk.EventType._2BUTTON_PRESS:
            self.ask_question()
        elif event.type == Gdk.EventType.BUTTON_PRESS:
            self.say_bubble(random.choice(TAUNTS), seconds=4)
        return True

    def _popup_menu(self, event):
        menu = Gtk.Menu()
        item_quiz = Gtk.MenuItem(label="Quiz me now")
        item_quiz.connect("activate", lambda i: self.ask_question())
        item_voice = Gtk.CheckMenuItem(label="Voice")
        item_voice.set_active(self.voice_on)
        item_voice.connect("toggled", lambda i: setattr(self, "voice_on", i.get_active()))
        item_quit = Gtk.MenuItem(label="Banish him (Quit)")
        item_quit.connect("activate", Gtk.main_quit)
        for it in (item_quiz, item_voice, Gtk.SeparatorMenuItem(), item_quit):
            menu.append(it)
        menu.show_all()
        try:
            menu.popup_at_pointer(event)
        except AttributeError:
            menu.popup()


streak_lines = [
    "You vanished for {missed} day(s). Your {streak}-day streak is dead. We start from zero.",
    "{missed} day(s) of silence. Streak: {streak} → 0. The syllabus noticed.",
]


def main():
    p = argparse.ArgumentParser(description="GRIM — the STRESS desktop reaper")
    p.add_argument("--size", type=int, default=190, help="sprite height in px")
    p.add_argument("--min-gap", type=float, default=4, help="min minutes between quizzes")
    p.add_argument("--max-gap", type=float, default=9, help="max minutes between quizzes")
    p.add_argument("--no-voice", dest="voice", action="store_false",
                   help="disable spoken lines (spd-say)")
    p.add_argument("--test", action="store_true",
                   help="rapid-fire demo: quiz in 8s, then every ~30s")
    p.add_argument("--speed", type=float, default=1.0, help="roam speed multiplier")
    cfg = p.parse_args()
    cfg.min_gap *= 60  # minutes -> seconds
    cfg.max_gap *= 60
    if cfg.min_gap > cfg.max_gap:
        cfg.min_gap, cfg.max_gap = cfg.max_gap, cfg.min_gap

    if DEBUG:
        print(f"grim: starting (backend={os.environ.get('GDK_BACKEND')}, "
              f"sprite={cfg.size}px)", flush=True)
    try:
        Reaper(cfg)
    except Exception as e:
        raise SystemExit(f"could not open a window: {e}\n"
                         "(needs a running X session / XWayland)")
    Gtk.main()


if __name__ == "__main__":
    main()
